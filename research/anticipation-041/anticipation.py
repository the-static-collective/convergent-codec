"""AT1: bounded causal verification scheduling and evidence-age gating over CT1."""
from collections import Counter
from context import Context
from analogy import need, apply
POLICIES=('periodic','random','burst','adaptive','learned','phase','paced')

class Rates:
    """Observed prediction disagreement per probe, not latent change hazard."""
    def __init__(self): self.counts=Counter();self.bad=Counter()
    @staticmethod
    def key(cue,age):return (int(bool(cue)),min(2,max(0,age)//3))
    def add(self,cue,age,wrong):
        k=self.key(cue,age);self.counts[k]+=1;self.bad[k]+=int(wrong)
    def rate(self,cue,age):
        k=self.key(cue,age);return (1+self.bad[k])/(2+self.counts[k])
    def report(self):return [{'cue':k[0],'age_bin':k[1],'n':n,'wrong':self.bad[k],'rate':self.rate(k[0],k[1]*3)} for k,n in sorted(self.counts.items())]

class Anticipation:
    def __init__(self,n,policy='periodic',width=10,budget=3,rates=None,seed=0):
        import random
        need(policy in POLICIES and 1<=budget<=width<=100,'schedule bounds')
        self.g=Context(n,'active');self.policy=policy;self.width=width;self.budget=budget;self.rates=rates or Rates();self.rng=random.Random(seed)
        self.t=-1;self.used=0;self.last=None;self.label=None;self.changed=False;self.stats=Counter();self.random_slots=set();self.recent_bad=False;self.pending=False
    def boot(self,pairs,label):
        self.g.enter(label);self.label=label
        for x,y in pairs:self.g.observe(x,y)
        if pairs:self.last=-1
    def age(self):return self.t-self.last if self.last is not None else self.width+1
    def step(self,label,cue):
        need(not self.pending,'scheduled observation must be supplied')
        self.t+=1;pos=self.t%self.width
        if pos==0:
            self.used=0
            if self.policy=='random':self.random_slots=set(self.rng.sample(range(self.width),self.budget))
        self.changed=label!=self.label;self.label=label;self.g.enter(label)
        if self.changed:self.last=None
        left=self.budget-self.used;remaining=self.width-pos
        if not left:return False
        if left==remaining:take=True
        elif self.policy=='periodic':take=pos in [i*self.width//self.budget for i in range(self.budget)]
        elif self.policy in ('phase','paced'):
            target=self.used*self.width//self.budget+1
            take=pos>=target or (self.policy=='paced' and pos==target-1 and (bool(cue) or self.changed))
        elif self.policy=='burst':take=pos<self.budget
        elif self.policy=='random':take=pos in self.random_slots
        else:
            age=self.age();spacing=max(1,self.width//self.budget)
            if self.policy=='adaptive':take=self.changed or bool(cue) or age>=spacing or (self.recent_bad and age>=1)
            else:take=self.changed or age>=spacing+1 or (age>=1 and self.rates.rate(cue,age)>=0.18)
        if take:self.used+=1;self.pending=True;self.stats['probes']+=1
        return take
    def probe(self,pool):
        need(self.pending,'no scheduled probe');return self.g.probe(pool)
    def observe(self,x,y):
        need(self.pending,'no scheduled observation');pred,_=self.g.predict(x)
        self.recent_bad=pred is not None and pred!=y
        self.stats['probe_disagreements']+=int(self.recent_bad);self.stats['comparable_probes']+=int(pred is not None)
        self.g.observe(x,y);self.last=self.t;self.pending=False
        return pred
    def predict(self,x,max_age=None):
        need(not self.pending,'scheduled observation must precede prediction')
        if max_age is not None:need(type(max_age) is int and max_age>=0,'age limit')
        y,basis=self.g.predict(x)
        if y is not None and max_age is not None and (self.last is None or self.age()>max_age):return None,'stale-abstention'
        return y,basis
