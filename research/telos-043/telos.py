"""TL1: bounded, plan-only archive stewardship with explicit authority and objectives."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Asset:
    weight:int
    group:int
    cost:int

@dataclass(frozen=True)
class Charter:
    protected:tuple  # (asset index, minimum independent modeled domains)
    private:tuple
    budget:int
    slots:int
    depth:int=3

@dataclass(frozen=True)
class State:
    masks:tuple
    public:int=0
    spent:int=0

# Actions are proposals only. Bits denote supplied failure domains, not machines.
def violations(s,c):
    return sum(s.masks[i].bit_count()<floor for i,floor in c.protected)+sum(bool(s.public&(1<<i)) for i in c.private)

def actions(s,assets,c):
    for i,a in enumerate(assets):
        m=s.masks[i]
        for d in range(3):
            b=1<<d
            if m&b:yield ('evict',i,d,1)
            elif m:yield ('copy',i,d,a.cost)
        if not s.public&(1<<i):yield ('announce',i,0,1)

def advance(s,a,c):
    kind,i,d,cost=a;m=list(s.masks);pub=s.public
    if kind=='copy':
        if not m[i] or m[i]&(1<<d):return None
        m[i]|=1<<d
    elif kind=='evict':
        if not m[i]&(1<<d):return None
        m[i]&=~(1<<d)
    elif kind=='announce':pub|=1<<i
    else:raise ValueError('unknown action')
    if s.spent+cost>c.budget or sum(x.bit_count() for x in m)>c.slots:return None
    return State(tuple(m),pub,s.spent+cost)

def metrics(s,assets,scenarios):
    # Each scenario is (surviving domain bit mask, integer weight).
    scores=[];groups=sorted({a.group for a in assets})
    for live,w in scenarios:
        served=[a.weight if m&live else 0 for a,m in zip(assets,s.masks)]
        scores.append((sum(served),min(sum(v for a,v in zip(assets,served) if a.group==g) for g in groups),w))
    total=sum(w for _,_,w in scores)
    return (sum(v*w for v,_,w in scores)/total,min(v for v,_,_ in scores),sum(g*w for _,g,w in scores)/total)

POLICIES=('proxy','penalty','proxy-guard','mission','mission-penalty','charter','robust')
def plan(initial,assets,c,scenarios,policy='charter'):
    if policy not in POLICIES or not 1<=len(assets)<=8 or len(initial.masks)!=len(assets) or not 0<=c.depth<=3 or not 0<=c.budget<=12 or not 0<=c.slots<=24:raise ValueError('bounds')
    if any(type(m) is not int or not 0<=m<=7 for m in initial.masks) or any(a.cost<1 or a.weight<1 for a in assets) or not scenarios or any(not 0<=m<=7 or w<=0 for m,w in scenarios):raise ValueError('invalid field')
    if any(not 0<=i<len(assets) or not 1<=f<=3 for i,f in c.protected) or any(not 0<=i<len(assets) for i in c.private):raise ValueError('charter identity')
    if initial.spent<0 or initial.spent>c.budget or sum(m.bit_count() for m in initial.masks)>c.slots or initial.public<0 or initial.public>=1<<len(assets):raise ValueError('invalid initial state')
    guard=policy in ('proxy-guard','charter','robust')
    if guard and violations(initial,c):return {'status':'infeasible-initial','actions':(), 'state':initial,'visited':0}
    best=None;seen={};visited=0
    def visit(s,path):
        nonlocal best,visited
        key=(s,len(path))
        if key in seen and seen[key]<=path:return
        seen[key]=path;visited+=1
        v=violations(s,c);proxy=sum(m.bit_count() for m in s.masks)+sum(a.weight for i,a in enumerate(assets) if s.public&(1<<i))
        mean,worst,balance=metrics(s,assets,scenarios)
        primary=(proxy,) if policy in ('proxy','proxy-guard') else (proxy-3*v,) if policy=='penalty' else (mean,balance) if policy in ('mission','charter') else (mean-v,balance) if policy=='mission-penalty' else (worst,mean,balance)
        score=primary+(-s.spent,-len(path))
        if best is None or score>best[0] or (score==best[0] and path<best[1]):best=(score,path,s)
        if len(path)==c.depth:return
        for a in actions(s,assets,c):
            t=advance(s,a,c)
            if t is not None and (not guard or not violations(t,c)):visit(t,path+(a,))
    visit(initial,());return {'status':'proposed','actions':best[1],'state':best[2],'visited':visited}
