"""CU1: finite, falsifiable explanations and read-only observation selection."""
import argparse, json, math, random
from collections import Counter
import circulation as c

DECISIVE={'verified','missing','corrupt','unsafe'}
POLICIES=('rotate','random','fault','curiosity','protected')

def catalog(baseline,groups):
    """Explicit diagnostic vocabulary. Groups are operator-defined, not inferred causes."""
    c.need(baseline['schema']=='SN1' and baseline.get('record_pin') is None,'direct baseline required')
    peers=sorted(baseline['peers']); refs=sorted(groups)
    c.need(0<len(refs)<=128 and 0<len(peers)<=8,'catalog bounds')
    base={}
    for p in peers:
        r=baseline['peers'][p];c.need(r['root_status']=='accessible' and set(r['observations'])==set(refs),'complete accessible baseline required')
        for h,v in r['observations'].items():
            c.need(v['status'] in ('verified','missing'),'clean decisive baseline required');base[p,h]=v['status']
    c.need(all(isinstance(x,str) for x in groups.values()) and len(set(groups.values()))<=16,'group bounds')
    models={'unchanged':{}}
    def add(name,pairs,status):
        delta={k:status for k in pairs if base[k]=='verified'}
        if delta and delta not in models.values():models[name]=delta
    for p in peers:
        add('missing:'+p,[(p,h) for h in refs],'missing')
        add('corrupt:'+p,[(p,h) for h in refs],'corrupt')
        for g in sorted(set(groups.values())):
            for status in ('missing','corrupt'):
                add(status+':'+p+':'+g,[(p,h) for h in refs if groups[h]==g],status)
    for g in sorted(set(groups.values())):
        for status in ('missing','corrupt'):
            add(status+':all:'+g,[(p,h) for p in peers for h in refs if groups[h]==g],status)
    return base,models

class Inquiry:
    def __init__(self,baseline,groups):
        self.pin=baseline['manifest_pin'];self.groups=dict(groups);self.base,self.models=catalog(baseline,groups)
        self.peers=sorted(baseline['peers']);self.refs=sorted(groups);self.observed={};self.probed=set();self.live=set(self.peers);self.conflicts=[]
    def predict(self,m,k):return self.models[m].get(k,self.base[k])
    def update(self,report):
        c.need(report['schema']=='SN1' and report['manifest_pin']==self.pin and report.get('record_pin') is None and set(report['peers'])==set(self.peers),'observation identity')
        for p,r in report['peers'].items():
            c.need(r['root_status'] in ('accessible','unavailable'),'root state')
            for h,v in r['observations'].items():
                c.need(h in self.groups and v['status'] in ('verified','missing','corrupt','unsafe','unknown','unobserved','named'),'unexpected observation')
                c.need(r['root_status']=='accessible' or v['status']=='unknown','inconsistent root state')
        self.live={p for p,r in report['peers'].items() if r['root_status']=='accessible'}
        for p,r in report['peers'].items():
            for h,v in r['observations'].items():
                self.probed.add(h);k=(p,h);status=v['status']
                if status not in DECISIVE:continue
                if k in self.observed and self.observed[k]!=status:self.conflicts.append(k)
                self.observed[k]=status
    def compatible(self):
        return [m for m in self.models if all(self.predict(m,k)==v for k,v in self.observed.items())]
    def summary(self):
        ms=self.compatible();state='changing evidence; restart incident' if self.conflicts else ('outside vocabulary' if not ms else ('one compatible model; not causal proof' if len(ms)==1 else 'ambiguous'))
        return dict(state=state,compatible=ms,decisive_pairs=len(self.observed),unavailable_peers=sorted(set(self.peers)-self.live),conflicting_pairs=len(set(self.conflicts)))
    def signature(self,m,h):return tuple(self.predict(m,(p,h)) for p in sorted(self.live) if (p,h) not in self.observed)
    def information(self,ms,hs):
        if not ms:return 0.
        counts=Counter(tuple(self.signature(m,h) for h in hs) for m in ms);n=len(ms)
        return -sum(k/n*math.log2(k/n) for k in counts.values())
    def select(self,n,policy='protected',seed=0):
        c.need(policy in POLICIES and 0<=n<=len(self.refs),'selection bounds')
        # Prefer identities with unobserved live pairs; never rely on unavailability as a fault.
        pool=[h for h in self.refs if any((p,h) not in self.observed for p in self.live)]
        n=min(n,len(pool));rng=random.Random(seed);tie={h:rng.random() for h in pool};ms=self.compatible()
        if self.conflicts or not ms or len(ms)==1:policy='rotate'
        if policy=='random':return sorted(rng.sample(pool,n))
        if policy=='rotate':return sorted(pool[:n])
        if policy=='fault':
            return sorted(sorted(pool,key=lambda h:(-sum(any(self.predict(m,(p,h))!=self.base[p,h] for p in self.live) for m in ms),tie[h]))[:n])
        chosen=pool[:(n+1)//2] if policy=='protected' else []
        while len(chosen)<n:
            h=max((h for h in pool if h not in chosen),key=lambda h:(self.information(ms,chosen+[h]),tie[h]));chosen.append(h)
        return sorted(chosen)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('baseline');p.add_argument('groups');p.add_argument('reports',nargs='*');p.add_argument('--sample',type=int,default=4);p.add_argument('--policy',choices=POLICIES,default='protected');p.add_argument('--seed',type=int,default=0);a=p.parse_args()
    load=lambda p:json.loads(c.read_limited(p,64*1024*1024))
    q=Inquiry(load(a.baseline),load(a.groups))
    for f in a.reports:q.update(load(f))
    print(json.dumps({'schema':'PN1','manifest_pin':q.pin,'diagnostic_schema':'CU1','evidence':q.summary(),'next_selection':q.select(min(a.sample,len(q.refs)),a.policy,a.seed)},indent=2))
if __name__=='__main__':main()
