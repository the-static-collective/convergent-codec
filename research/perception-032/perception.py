"""PN1 longitudinal observation and bounded attention; no repair or deletion."""
import argparse, json, hashlib, random
from collections import Counter
from pathlib import Path
import circulation as c
import sensation as s

DECISIVE={'verified','missing','corrupt','unsafe'}
FAULT={'missing','corrupt','unsafe'}
class Ledger:
    def __init__(self,pin,refs,peers):
        c.need(c.valid_hash(pin) and len(refs)<=c.MAX_OBJECTS and all(c.valid_hash(h) for h in refs),'invalid references')
        c.need(len(set(refs))==len(refs) and 0<len(peers)<=s.MAX_PEERS and len(set(peers))==len(peers),'invalid peers or references')
        self.pin=pin;self.refs=sorted(refs);self.peers=sorted(peers);self.tick=-1;self.head='0'*64;self.rows={};self.root={};self.history=[];self.transitions=Counter();self.root_pairs=Counter()
    def update(self,report):
        c.need(report['schema']=='SN1' and report['manifest_pin']==self.pin and report.get('record_pin') is None,'report identity mismatch')
        c.need(set(report['peers'])==set(self.peers),'peer labels changed')
        for p,r in report['peers'].items():
            c.need(r['root_status'] in ('accessible','unavailable') and set(r['observations'])<=set(self.refs),'unexpected observation')
            for h,v in r['observations'].items():
                c.need(v['status'] in s.STATES and (r['root_status']=='accessible' or v['status']=='unknown'),'unexpected state')
        self.tick+=1;out={}
        for p,r in sorted(report['peers'].items()):
            prevroot=self.root.get(p);self.root[p]=r['root_status'];tested=lost=bad=0
            for h,v in sorted(r['observations'].items()):
                status=v['status'];row=self.rows.setdefault((p,h),{'last':None,'last_tick':-1,'decisive':None,'decisive_tick':-1,'ever_verified':False,'faults':0,'tests':0})
                if status in DECISIVE:
                    if row['decisive'] is not None:
                        gap=self.tick-row['decisive_tick'];self.transitions[(p,gap,row['decisive'],status)]+=1
                    if row['decisive']=='verified':tested+=1;lost+=status=='missing'
                    if status in FAULT and row['ever_verified'] and row['decisive']=='verified':row['faults']+=1
                    bad+=status in ('corrupt','unsafe');row['tests']+=1;row['decisive']=status;row['decisive_tick']=self.tick
                    row['ever_verified']|=status=='verified'
                row['last']=status;row['last_tick']=self.tick
            # Candidate explanations, not permanent-loss or causal claims.
            if r['root_status']=='unavailable':kind='inaccessible; contents unknown'
            elif tested>=2 and lost/tested>=.75:kind='many previously verified copies now missing; investigate removal or remount'
            elif bad:kind='integrity fault observed'
            elif lost:kind='previously verified copies now missing'
            elif prevroot=='unavailable':kind='accessible again; untested contents unknown'
            else:kind='no sampled transition establishes a fault'
            out[p]={'interpretation':kind,'previously_verified_retested':tested,'now_missing':lost,'bad':bad}
        for i,p in enumerate(self.peers):
            for q in self.peers[i+1:]:self.root_pairs[(p,q,self.root[p],self.root[q])]+=1
        receipt={'tick':self.tick,'previous':self.head,'report_sha256':c.digest(c.canon(report)),'interpretations':out}
        self.head=c.digest(c.canon(receipt));receipt['sha256']=self.head;self.history.append(receipt);return receipt
    def summary(self):
        return {'transitions':[{'peer':p,'gap_ticks':g,'from':a,'to':b,'count':n} for (p,g,a,b),n in sorted(self.transitions.items())],'root_coobservations':[{'peers':[p,q],'states':[a,b],'count':n} for (p,q,a,b),n in sorted(self.root_pairs.items())],'note':'Observed counts only; adaptive selection, missing observations and interval censoring prevent direct hazard inference.'}
    def priority(self,h):
        rows=[self.rows.get((p,h),{}) for p in self.peers]
        age=max((self.tick-r.get('decisive_tick',-1) for p,r in zip(self.peers,rows) if self.root.get(p)!='unavailable'),default=0)
        # Last-known evidence is not a statement of current possession.
        live=sum(r.get('decisive')=='verified' and self.root.get(p)=='accessible' for p,r in zip(self.peers,rows))
        history=sum(r.get('faults',0) for r in rows)
        return age,history,live
    def select(self,n,policy='rotate',seed=0):
        c.need(0<=n<=len(self.refs) and policy in ('random','rotate','adaptive','age'),'invalid sampling')
        rng=random.Random(seed);tie={h:rng.random() for h in self.refs}
        if policy=='random':return sorted(rng.sample(self.refs,n))
        if policy=='rotate':
            start=max(0,self.tick)*n%max(1,len(self.refs));return sorted((self.refs+self.refs)[start:start+n])
        # Reserve half of attention for oldest evidence. Fault history drives the rest.
        scores={h:self.priority(h) for h in self.refs};old=sorted(self.refs,key=lambda h:(-scores[h][0],tie[h]))
        if policy=='age':return sorted(old[:n])
        chosen=old[:(n+1)//2];remaining=set(self.refs)-set(chosen)
        chosen+=sorted(remaining,key=lambda h:(-(min(3,scores[h][1])*3+scores[h][0]+max(0,2-scores[h][2])),tie[h]))[:n-len(chosen)]
        return sorted(chosen)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest');p.add_argument('pin');p.add_argument('reports',nargs='+');p.add_argument('--sample',type=int,default=8);p.add_argument('--policy',choices=['adaptive','age','random','rotate'],default='rotate');p.add_argument('--seed',type=int,default=0);a=p.parse_args()
    m=json.loads(c.read_limited(a.manifest,c.MAX_MANIFEST));refs=c.validate(m);c.need(c.digest(c.canon(m))==a.pin,'manifest pin mismatch')
    ledger=None
    for path in a.reports:
        report=json.loads(c.read_limited(path,64*1024*1024));ledger=ledger or Ledger(a.pin,refs,report['peers']);ledger.update(report)
    print(json.dumps({'schema':'PN1','manifest_pin':a.pin,'head':ledger.head,'receipts':ledger.history,'evidence_summary':ledger.summary(),'next_selection':ledger.select(min(a.sample,len(refs)),a.policy,a.seed)},indent=2))
if __name__=='__main__':main()
