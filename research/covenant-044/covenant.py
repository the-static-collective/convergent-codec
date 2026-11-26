"""CV1: signed, scoped, plan-only authorization. Trusted head/time/state are external."""
import hashlib,json,re
from dataclasses import asdict
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature
import telos as t
ZERO='0'*64
LIMIT=1024
OPS=('copy','evict','announce')
class Rejected(ValueError):pass
def need(ok,msg):
    if not ok:raise Rejected(msg)
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()
def digest(x):return hashlib.sha256(canon(x)).hexdigest()
def key(k):return k.public_key().public_bytes_raw().hex()
def hexstr(x,n):return isinstance(x,str) and re.fullmatch('[0-9a-f]{'+str(n)+'}',x) is not None
def ident(x):return isinstance(x,str) and re.fullmatch(r'[A-Za-z0-9_.:-]{1,80}',x) is not None
def integer(x,lo,hi):return type(x) is int and lo<=x<=hi
def shape(x,fields):need(isinstance(x,dict) and set(x)==set(fields.split()),'unexpected fields')
def signed(k,body,kind):
    b=canon(body);need(len(b)<=65536,'record size');return {'body':body,'sig':k.sign(b'CV1:'+kind.encode()+b':'+b).hex()}
def check(record,kind):
    shape(record,'body sig');b=record['body'];need(isinstance(b,dict) and hexstr(b.get('issuer'),64) and hexstr(record['sig'],128),'signature shape')
    data=canon(b);need(len(data)<=65536,'record size')
    try:Ed25519PublicKey.from_public_bytes(bytes.fromhex(b['issuer'])).verify(bytes.fromhex(record['sig']),b'CV1:'+kind.encode()+b':'+data)
    except InvalidSignature as e:raise Rejected('signature invalid') from e
    return b

def event(k,ledger,seq,prev,at,kind,data):return signed(k,dict(issuer=key(k),ledger=ledger,seq=seq,prev=prev,at=at,kind=kind,data=data),'event')

def charter_data(names,domains,assets,charter):
    return json.loads(canon(dict(names=list(names),domains=list(domains),assets=[asdict(a) for a in assets],charter=asdict(charter))))
def parse_charter(d):
    shape(d,'names domains assets charter');ns,ds,aa,ch=d['names'],d['domains'],d['assets'],d['charter']
    need(isinstance(ns,list) and 1<=len(ns)<=8 and all(ident(n) for n in ns) and len(set(ns))==len(ns),'asset names')
    need(isinstance(ds,list) and len(ds)==3 and all(ident(n) for n in ds) and len(set(ds))==3 and 'public' not in ds,'domains')
    need(isinstance(aa,list) and len(aa)==len(ns),'assets');assets=[]
    for a in aa:
        shape(a,'weight group cost');need(integer(a['weight'],1,1000000) and integer(a['group'],0,1000000) and integer(a['cost'],1,12),'asset bounds');assets.append(t.Asset(**a))
    shape(ch,'protected private budget slots depth');p=ch['protected'];v=ch['private']
    need(isinstance(p,list) and all(isinstance(x,list) and len(x)==2 and integer(x[0],0,len(ns)-1) and integer(x[1],1,3) for x in p),'protected')
    need(isinstance(v,list) and all(integer(x,0,len(ns)-1) for x in v),'private')
    need(len({x[0] for x in p})==len(p) and len(set(v))==len(v),'duplicate charter entries')
    need(integer(ch['budget'],0,12) and integer(ch['slots'],0,24) and integer(ch['depth'],0,3),'charter bounds')
    return tuple(ns),tuple(ds),tuple(assets),t.Charter(tuple(map(tuple,p)),tuple(v),ch['budget'],ch['slots'],ch['depth'])

class Ledger:
    def __init__(self,root,ledger,records,head,now):
        need(hexstr(root,64) and ident(ledger) and hexstr(head,64) and integer(now,0,2**53-1),'trust anchor')
        need(isinstance(records,list) and 0<len(records)<=LIMIT,'ledger bounds')
        self.root=root;self.ledger=ledger;self.now=now;self.head=ZERO;self.at=0;self.grants={};self.denies={};self.revoked=set();self.charter_id=None
        for i,r in enumerate(records):
            b=check(r,'event');shape(b,'issuer ledger seq prev at kind data');need(b['ledger']==ledger and integer(b['seq'],i,i) and b['prev']==self.head and integer(b['at'],self.at,now),'chain/time mismatch')
            self.at=b['at'];rid=digest(r);self.add(b,rid);self.head=rid
        need(self.head==head and self.charter_id is not None,'head or charter mismatch')
    def scopes(self,ss):
        need(isinstance(ss,list) and 1<=len(ss)<=len(self.names)*7,'scope count');out=set()
        for s in ss:
            need(isinstance(s,list) and len(s)==3 and all(isinstance(x,str) for x in s),'scope shape');op,n,d=s
            need(op in OPS and n in self.names and (d=='public' if op=='announce' else d in self.domains),'scope outside charter field');out.add(tuple(s))
        need(len(out)==len(ss),'duplicate scope');return frozenset(out)
    def interval(self,d):
        need(integer(d['start'],self.at,2**53-1) and integer(d['end'],d['start']+1,2**53-1),'interval')
    def active(self,r,at):return r['charter']==self.charter_id and r['start']<=at<r['end']
    def denied(self,actor,scope,at):
        return sorted(i for i,r in self.denies.items() if i not in self.revoked and self.active(r,at) and r['subject']==actor and scope in r['scopes'])
    def path(self,gid,scope,at):
        out=[]
        while gid is not None:
            g=self.grants.get(gid)
            if g is None or gid in self.revoked or not self.active(g,at) or scope not in g['scopes'] or self.denied(g['subject'],scope,at):return None
            out.append(gid);gid=g['parent']
        return tuple(out)
    def add(self,b,rid):
        k,d,issuer=b['kind'],b['data'],b['issuer']
        if k=='charter':
            need(issuer==self.root,'root-only charter');shape(d,'previous field');need(d['previous']==self.charter_id,'charter lineage')
            self.names,self.domains,self.assets,self.charter=parse_charter(d['field']);self.charter_id=rid;return
        need(self.charter_id is not None,'charter required first')
        if k in ('grant','deny'):
            shape(d,'charter subject scopes start end parent delegate' if k=='grant' else 'charter subject scopes start end')
            need(d['charter']==self.charter_id and hexstr(d['subject'],64),'subject or charter');self.interval(d);ss=self.scopes(d['scopes']);r=dict(d,scopes=ss,issuer=issuer)
            if k=='deny':need(issuer==self.root,'root-only denial');self.denies[rid]=r;return
            need(type(d['delegate']) is bool,'delegate flag');p=d['parent']
            if p is None:need(issuer==self.root,'root-only unparented grant')
            else:
                need(hexstr(p,64) and p in self.grants,'unknown parent');g=self.grants[p]
                need(g['subject']==issuer and g['delegate'] and g['start']<=d['start']<d['end']<=g['end'] and ss<=g['scopes'],'delegation expansion')
                need(all(self.path(p,s,self.at) is not None for s in ss),'parent not effective at issuance')
            self.grants[rid]=r;return
        if k=='revoke':
            shape(d,'target');i=d['target'];need(hexstr(i,64),'revocation target');r=self.grants.get(i) or self.denies.get(i)
            need(r is not None and i not in self.revoked and (issuer==self.root or issuer==r['issuer']),'revocation authority');self.revoked.add(i);return
        raise Rejected('unknown event')
    def authorize(self,actor,scope):
        need(hexstr(actor,64) and isinstance(scope,tuple) and len(scope)==3,'authorization shape')
        denies=self.denied(actor,scope,self.now)
        paths=[p for i,g in self.grants.items() if g['subject']==actor for p in [self.path(i,scope,self.now)] if p]
        if denies:return {'status':'prohibited','denials':denies,'paths':[]}
        if paths:return {'status':'permitted','paths':[list(p) for p in sorted(paths)],'denials':[]}
        return {'status':'unresolved','paths':[],'denials':[]}
    def scope(self,a):return (a[0],self.names[a[1]],'public' if a[0]=='announce' else self.domains[a[2]])

def state_hash(s,observation_pin):
    need(hexstr(observation_pin,64),'observation pin');return digest(dict(state=asdict(s),observation=observation_pin))
def valid_state(l,s):
    c=l.charter;need(len(s.masks)==len(l.assets) and all(integer(m,0,7) for m in s.masks) and integer(s.spent,0,c.budget) and integer(s.public,0,2**len(l.assets)-1) and sum(m.bit_count() for m in s.masks)<=c.slots and not t.violations(s,c),'invalid or infeasible initial state')
def proposal(k,l,s,obs,actions,until):
    return signed(k,dict(issuer=key(k),ledger=l.ledger,head=l.head,charter=l.charter_id,state=state_hash(s,obs),at=l.now,until=until,actions=[list(a) for a in actions]),'proposal')
def verify(l,s,obs,p):
    valid_state(l,s);b=check(p,'proposal');shape(b,'issuer ledger head charter state at until actions')
    need(b['ledger']==l.ledger and b['head']==l.head and b['charter']==l.charter_id and b['state']==state_hash(s,obs),'stale or wrong proposal binding')
    need(integer(b['at'],0,l.now) and integer(b['until'],l.now+1,2**53-1) and b['at']<b['until'],'proposal time')
    aa=b['actions'];need(isinstance(aa,list) and len(aa)<=l.charter.depth,'proposal depth');out=[]
    for a in aa:
        need(isinstance(a,list) and len(a)==4 and isinstance(a[0],str) and all(type(x) is int for x in a[1:]),'action shape');a=tuple(a)
        need(a in set(t.actions(s,l.assets,l.charter)),'invalid action or cost');auth=l.authorize(b['issuer'],l.scope(a));need(auth['status']=='permitted','action '+auth['status'])
        nxt=t.advance(s,a,l.charter);need(nxt is not None and not t.violations(nxt,l.charter),'charter or resource violation');out.append(dict(action=list(a),scope=l.scope(a),authorization=auth,state=asdict(nxt)));s=nxt
    return dict(schema='CV1',status='verified-proposal-only',proposal=digest(p),head=l.head,charter=l.charter_id,at=l.now,steps=out,final=asdict(s))

def plan(l,actor,s,scenarios):
    valid_state(l,s);need(hexstr(actor,64) and bool(scenarios) and all(integer(m,0,7) and integer(w,1,1000000) for m,w in scenarios),'planning field')
    c=l.charter;allowed={scope:l.authorize(actor,scope)['status']=='permitted' for op in OPS for n in l.names for d in (('public',) if op=='announce' else l.domains) for scope in [(op,n,d)]};best=None;seen=set()
    def visit(state,path):
        nonlocal best
        if (state,len(path)) in seen:return
        seen.add((state,len(path)));mean,worst,balance=t.metrics(state,l.assets,scenarios);score=(mean,balance,-state.spent,-len(path))
        if best is None or score>best[0]:best=(score,path,state)
        if len(path)==c.depth:return
        for a in t.actions(state,l.assets,c):
            if not allowed[l.scope(a)]:continue
            nxt=t.advance(state,a,c)
            if nxt is not None and not t.violations(nxt,c):visit(nxt,path+(a,))
    visit(s,());return {'actions':best[1],'state':best[2],'visited':len(seen)}
