"""KR1: bounded decision under explicitly assumed opportunity dynamics. No I/O or actions."""
from dataclasses import dataclass
from functools import lru_cache
from math import isfinite

@dataclass(frozen=True)
class Model:
    rise:float; fall:float; cue_good:float; cue_bad:float; test_good:float; test_bad:float
    def __post_init__(self):
        if not all(isfinite(x) and 0<=x<=1 for x in vars(self).values()):raise ValueError('probability bounds')

@dataclass(frozen=True)
class Offer:
    gain:float=12; loss:float=18; decay:float=.18; probe_cost:float=.7; reserve_cost:float=1.3; horizon:int=4; probes:int=2
    def __post_init__(self):
        if not all(isfinite(x) and x>=0 for x in (self.gain,self.loss,self.probe_cost,self.reserve_cost)) or not 0<=self.decay<=1 or type(self.horizon) is not int or not 1<=self.horizon<=5 or type(self.probes) is not int or not 0<=self.probes<=2:raise ValueError('offer bounds')

# Belief is a joint distribution over (model, bad/good). Model identity is fixed during an episode.
def initial(models,p=.5):
    if not 1<=len(models)<=3 or not 0<=p<=1:raise ValueError('belief bounds')
    return tuple(v/len(models) for _ in models for v in (1-p,p))
def observe(models,b,kind,y):
    if kind not in ('cue','test') or y not in (0,1):raise ValueError('observation')
    probs=[getattr(m,kind+'_'+s) for m in models for s in ('bad','good')];q=tuple(w*(p if y else 1-p) for w,p in zip(b,probs));z=sum(q)
    return z,tuple(v/z for v in q) if z else None

def advance(models,b):
    out=[]
    for i,m in enumerate(models):
        a,g=b[2*i:2*i+2];out.extend((a*(1-m.rise)+g*m.fall,a*m.rise+g*(1-m.fall)))
    return tuple(out)

def start(o):return (o.horizon,0,False,o.probes)
def actions(state):
    h,age,locked,n=state
    return ('decline','commit')+ (('wait',) if h>1 else ()) + (('inspect',) if h>1 and n else ()) + (('reserve',) if not locked else ())
def next_state(s,a):
    h,age,locked,n=s
    if a not in actions(s) or a in ('commit','decline'):raise ValueError('invalid transition')
    # Reservation costs a fee, locks current gain and extends expiry by one tick;
    # after reserving the operator can still decline. No rollback of a commitment.
    return (h if a=='reserve' else h-1,age if locked or a=='reserve' else age+1,locked or a=='reserve',n-(a=='inspect'))
def payoff(o,s,g):return o.gain*(1-o.decay)**s[1] if g else -o.loss
def commit(o,s,b):
    p=sum(b[1::2]);return p*payoff(o,s,1)+(1-p)*payoff(o,s,0)
def fee(o,a):return o.probe_cost if a=='inspect' else o.reserve_cost if a=='reserve' else 0.

def branches(models,b,a):
    # Inspect measures current state, then time passes. Cue measures next state.
    for z,p in ([(None,1.)] if a!='inspect' else [(y,observe(models,b,'test',y)[0]) for y in (0,1)]):
        if not p:continue
        bb=b if z is None else observe(models,b,'test',z)[1]
        for y in (0,1):
            q,bbb=observe(models,advance(models,bb),'cue',y)
            if q:yield z,y,p*q,bbb

class Planner:
    def __init__(self,models,offer):
        self.models=tuple(models);initial(self.models);self.offer=offer
        self.value=lru_cache(maxsize=100000)(self._value)
    def terminal(self,s,b):return max(0.,commit(self.offer,s,b))
    def values(self,s,b,depth=None):
        d={}
        for a in actions(s):
            if a=='decline':d[a]=0.
            elif a=='commit':d[a]=commit(self.offer,s,b)
            elif depth==0:continue
            else:
                ns=next_state(s,a);d[a]=-fee(self.offer,a)+sum(p*self.value(ns,bb,None if depth is None else depth-1) for z,y,p,bb in branches(self.models,b,a))
        return d
    def _value(self,s,b,depth=None):return max(self.values(s,b,depth).values())
    def choose(self,s,b,policy='plan'):
        if policy not in ('plan','myopic','greedy','inspect-first','wait-first','reserve-first'):raise ValueError('unknown policy')
        if policy.endswith('-first'):
            a=policy[:-6]
            if a in actions(s) and (a!='wait' or commit(self.offer,s,b)<=0):return a
        d=self.values(s,b,None if policy=='plan' else 1 if policy=='myopic' else 0)
        return max(d,key=d.get)
    def update(self,b,a,z,y):
        if a=='inspect':
            if z not in (0,1):raise ValueError('missing inspection')
            _,b=observe(self.models,b,'test',z)
            if b is None:return None
        elif z is not None:raise ValueError('unexpected inspection')
        return observe(self.models,advance(self.models,b),'cue',y)[1]

class GuardedPlanner(Planner):
    """Require nonnegative conditional expected commitment payoff in each live model.
    This is a model-relative commitment constraint, not a worst-case trajectory guarantee.
    """
    def values(self,s,b,depth=None):
        d=super().values(s,b,depth)
        if any(a+g>0 and g*payoff(self.offer,s,1)-a*self.offer.loss<0 for a,g in zip(b[::2],b[1::2])):d.pop('commit',None)
        return d
