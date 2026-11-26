"""RS1: plan-only gifts for relief and productive restoration; no repayment claims."""
from dataclasses import dataclass
from reciprocity import Offer,allocate,verify,need
POLICIES=('none','relief','productive','relief-first','shared','hybrid','guarded')
@dataclass(frozen=True)
class Project:
    id:int
    members:tuple
    cost:int
    yield_units:int
    delay:int

# A project is installed only when fully funded. Donors must consent to every beneficiary.
def plan(offers,gaps,projects,accepted,priority,policy='guarded'):
    n=len(offers);need(policy in POLICIES and 1<=n<=32 and len(gaps)==len(accepted)==len(priority)==n,'field')
    need(all(type(g) is int and 0<=g<=10000 for g in gaps),'gaps')
    need(all(type(a) is bool for a in accepted),'acceptance')
    for o in offers:need(all(type(v) is int and 0<=v<=10000 for v in (o.stock,o.floor,o.cap)) and all(type(j) is int and 0<=j<n for j in o.recipients),'offer')
    need(len(projects)<=64 and len({p.id for p in projects})==len(projects),'projects')
    for p in projects:need(type(p.id) is int and 0<=p.id<10000 and 1<=len(p.members)<=n and len(set(p.members))==len(p.members) and all(type(j) is int and 0<=j<n for j in p.members) and type(p.cost) is int and 1<=p.cost<=10000 and type(p.yield_units) is int and p.yield_units>0 and type(p.delay) is int and p.delay>=1,'project')
    supply=[min(o.cap,max(0,o.stock-o.floor)) for o in offers];sent=[0]*n;relief=[];funding=[];chosen=None
    def give():
        oo=[Offer(o.stock-sent[i],o.floor,o.cap-sent[i],o.recipients) for i,o in enumerate(offers)]
        aa=allocate(oo,gaps,gaps,[[0]*n for _ in range(n)],'gift')
        for i,j in aa:sent[i]+=1;relief.append((i,j))
    def invest():
        nonlocal chosen
        options=[]
        for p in projects:
            if policy in ('productive','relief-first') and len(p.members)!=1:continue
            if policy=='shared' and len(p.members)==1:continue
            if not all(accepted[j] for j in p.members):continue
            # Do not route a person's gift back to that same person.
            ds=[i for i,o in enumerate(offers) if i not in p.members and set(p.members)<=set(o.recipients) and supply[i]>sent[i]]
            if sum(supply[i]-sent[i] for i in ds)<p.cost:continue
            score=(sum(priority[j] for j in p.members)*p.yield_units/p.cost/(1+p.delay),-p.cost,-p.id)
            options.append((score,p,ds))
        if not options:return
        _,p,ds=max(options,key=lambda x:x[0]);chosen=p.id;left=p.cost
        for i in sorted(ds,key=lambda i:(-(supply[i]-sent[i]),i)):
            k=min(left,supply[i]-sent[i]);funding.extend([i]*k);sent[i]+=k;left-=k
            if not left:break
    if policy!='none':
        if policy in ('productive','shared','hybrid'):invest();give()
        else:
            give()
            if policy=='relief-first' or policy=='guarded' and len(relief)==sum(gaps):invest()
    result=(tuple(relief),chosen,tuple(funding));check(offers,gaps,projects,accepted,result);return result

def check(offers,gaps,projects,accepted,result):
    relief,pid,funding=result;sent,received=verify(offers,gaps,relief);sent=list(sent)
    if pid is None:need(not funding,'funding without project')
    else:
        pp=[p for p in projects if p.id==pid];need(len(pp)==1,'unknown project');p=pp[0]
        need(len(funding)==p.cost and all(accepted[j] for j in p.members),'partial or unaccepted project')
        for i in funding:
            need(type(i) is int and 0<=i<len(offers) and i not in p.members and set(p.members)<=set(offers[i].recipients),'investment consent');sent[i]+=1
    need(all(s<=min(o.cap,max(0,o.stock-o.floor)) for s,o in zip(sent,offers)),'combined quota')
    return tuple(sent),received
