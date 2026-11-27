"""FL1: independent signed offers, joint assent, plan-only cooperation."""
from dataclasses import asdict
import covenant as c
import telos as t
from collections import Counter

# A copy is (copy, asset index, source domain, destination domain); evict uses
# source domain and -1 destination; announce uses -1 for both. No wildcard.
def legal(s):
    for i,m in enumerate(s.masks):
        for d in range(3):
            if m & (1<<d):
                yield ('evict',i,d,-1)
                for e in range(3):
                    if not m & (1<<e):yield ('copy',i,d,e)
        if not s.public & (1<<i):yield ('announce',i,-1,-1)

def scope(a,n):
    c.need(isinstance(a,(tuple,list)) and len(a)==4,'scope shape');op,i,src,dst=a
    c.need(c.integer(i,0,n-1) and type(src) is int and type(dst) is int,'asset index')
    c.need((op=='copy' and c.integer(src,0,2) and c.integer(dst,0,2) and src!=dst) or (op=='evict' and c.integer(src,0,2) and dst==-1) or (op=='announce' and src==dst==-1),'scope')
    return tuple(a)

def formation(field,owners,custodians):
    return dict(field=field,owners=list(owners),custodians=list(custodians))

def endorse(k,agreement):return c.signed(k,dict(issuer=c.key(k),agreement=c.digest(agreement)),'fl-formation')

def offer(k,agreement,seq,prev,at,end,actor,scopes,units,withdraw=False):
    return c.signed(k,dict(issuer=c.key(k),agreement=c.digest(agreement),seq=seq,prev=prev,at=at,end=end,actor=actor,scopes=[list(a) for a in scopes],units=units,withdraw=withdraw),'fl-offer')

class Fellowship:
    def __init__(self,agreement,endorsements,chains,pin,heads,now):
        c.shape(agreement,'field owners custodians');c.need(c.digest(agreement)==pin and c.integer(now,0,2**53-1),'trust anchor')
        self.names,self.domains,self.assets,self.charter=c.parse_charter(agreement['field']);self.agreement=pin;self.now=now
        self.owners=tuple(agreement['owners']);self.custodians=tuple(agreement['custodians']);self.parties=set(self.owners+self.custodians)
        c.need(len(self.owners)==len(self.names) and len(self.custodians)==3 and all(c.hexstr(k,64) for k in self.parties),'participant keys')
        c.need(len(self.parties)<=11 and isinstance(endorsements,list) and len(endorsements)==len(self.parties),'formation quorum')
        seen=set()
        for r in endorsements:
            b=c.check(r,'fl-formation');c.shape(b,'issuer agreement');c.need(b['agreement']==pin and b['issuer'] in self.parties and b['issuer'] not in seen,'formation signature');seen.add(b['issuer'])
        c.need(set(chains)==set(heads)==self.parties,'independent current heads required');self.heads=dict(heads);self.offers={}
        for k in sorted(self.parties):
            seq=chains[k];c.need(isinstance(seq,list) and len(seq)<=128,'offer chain limit');prev=c.ZERO;at=0
            for i,r in enumerate(seq):
                b=c.check(r,'fl-offer');c.shape(b,'issuer agreement seq prev at end actor scopes units withdraw')
                c.need(b['issuer']==k and b['agreement']==pin and c.integer(b['seq'],i,i) and b['prev']==prev and c.integer(b['at'],at,now) and c.integer(b['end'],b['at']+1,2**53-1),'offer lineage/time')
                c.need(c.hexstr(b['actor'],64) and type(b['withdraw']) is bool and c.integer(b['units'],0,12) and isinstance(b['scopes'],list) and len(b['scopes'])<=len(self.names)*10,'offer bounds')
                ss=[scope(a,len(self.names)) for a in b['scopes']];c.need(len(set(ss))==len(ss) and all(k in self.required(a) for a in ss),'scope not controlled by issuer')
                c.need(not b['withdraw'] or not ss and b['units']==0,'withdrawal must be empty');at=b['at'];prev=c.digest(r);self.offers[k]=dict(b,scopes=frozenset(ss))
            c.need(prev==heads[k],'stale participant head')
    def required(self,a):
        op,i,src,dst=a;out={self.owners[i]}
        if src>=0:out.add(self.custodians[src])
        if dst>=0:out.add(self.custodians[dst])
        return out
    def cost(self,a):return self.assets[a[1]].cost if a[0]=='copy' else 1
    def advance(self,s,a):
        op,i,src,dst=a;return t.advance(s,(op,i,dst if op=='copy' else src if op=='evict' else 0,self.cost(a)),self.charter)
    def permit(self,actor,a,used):
        missing=[];withdrawn=[];limits=[]
        for k in sorted(self.required(a)):
            b=self.offers.get(k)
            if b is not None and b['withdraw']:withdrawn.append(k)
            elif b is None or b['end']<=self.now or b['actor']!=actor or a not in b['scopes']:missing.append(k)
            elif used.get(k,0)+self.cost(a)>b['units']:limits.append(k)
        return dict(status='withdrawn' if withdrawn else 'unresolved' if missing else 'limit' if limits else 'permitted',missing=missing,withdrawn=withdrawn,limits=limits)
    def valid(self,s):c.valid_state(self,s)
    def evaluate(self,actor,s,aa):
        self.valid(s);c.need(c.hexstr(actor,64) and isinstance(aa,(list,tuple)) and len(aa)<=self.charter.depth,'plan bounds');used=Counter();required=set();steps=[]
        for raw in aa:
            a=scope(raw,len(self.names));c.need(a in set(legal(s)),'invalid action');p=self.permit(actor,a,used);c.need(p['status']=='permitted',p['status']);nxt=self.advance(s,a);c.need(nxt is not None and not t.violations(nxt,self.charter),'charter violation');rs=self.required(a);required.update(rs)
            for k in rs:used[k]+=self.cost(a)
            steps.append(dict(action=a,required=sorted(rs),state=asdict(nxt)));s=nxt
        return dict(final=asdict(s),required=sorted(required),used=dict(used),steps=steps)
    def plan(self,actor,s,scenarios):
        self.valid(s);c.need(c.hexstr(actor,64) and bool(scenarios) and all(c.integer(m,0,7) and c.integer(w,1,1000000) for m,w in scenarios),'planning field');best=None;seen=set()
        def visit(z,path,used):
            nonlocal best
            k=(z,len(path),tuple(sorted(used.items())))
            if k in seen:return
            seen.add(k);mean,worst,balance=t.metrics(z,self.assets,scenarios);score=(mean,balance,-z.spent,-len(path))
            if best is None or score>best[0]:best=(score,path,z)
            if len(path)==self.charter.depth:return
            for a in legal(z):
                if self.permit(actor,a,used)['status']!='permitted':continue
                nxt=self.advance(z,a)
                if nxt is None or t.violations(nxt,self.charter):continue
                u=used.copy()
                for k in self.required(a):u[k]+=self.cost(a)
                visit(nxt,path+(a,),u)
        visit(s,(),Counter());return dict(actions=best[1],state=best[2],visited=len(seen))

def proposal(k,f,s,obs,aa,until):
    return c.signed(k,dict(issuer=c.key(k),agreement=f.agreement,heads=f.heads,state=c.state_hash(s,obs),at=f.now,until=until,actions=[list(a) for a in aa]),'fl-proposal')
def assent(k,p):return c.signed(k,dict(issuer=c.key(k),proposal=c.digest(p)),'fl-assent')
def verify(f,s,obs,p,assents):
    b=c.check(p,'fl-proposal');c.shape(b,'issuer agreement heads state at until actions');c.need(b['agreement']==f.agreement and b['heads']==f.heads and b['state']==c.state_hash(s,obs),'stale proposal binding');c.need(c.integer(b['at'],0,f.now) and c.integer(b['until'],f.now+1,2**53-1),'proposal time');r=f.evaluate(b['issuer'],s,b['actions']);seen=set();c.need(isinstance(assents,list) and len(assents)==len(r['required']),'joint assent count')
    for sig in assents:
        a=c.check(sig,'fl-assent');c.shape(a,'issuer proposal');c.need(a['proposal']==c.digest(p) and a['issuer'] in r['required'] and a['issuer'] not in seen,'joint assent mismatch');seen.add(a['issuer'])
    return dict(schema='FL1',status='verified-proposal-only',proposal=c.digest(p),agreement=f.agreement,heads=f.heads,at=f.now,**r)
