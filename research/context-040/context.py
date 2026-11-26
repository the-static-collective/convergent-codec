"""CT1 causal context-conditioned prediction, no I/O or automatic actions."""
from collections import Counter, OrderedDict
from math import log2
from analogy import Space, apply, vector, need
POLICIES=('static','reset','window','label','recall','active','cautious','active-reset')
class Context:
    def __init__(self,n,policy='active',capacity=4):
        need(policy in POLICIES and 1<=capacity<=16,'policy or capacity')
        self.n=n;self.policy=policy;self.capacity=capacity;self.cache=OrderedDict();self.labels=OrderedDict();self.label=None;self.pairs=[];self.space=Space(n);self.stats=Counter();self.selected=None
    def enter(self,label):
        need(isinstance(label,str) and len(label)<=128,'label')
        if label==self.label:return
        self.label=label
        if self.policy in ('reset','label','recall','active','cautious','active-reset'):
            self.pairs=[];self.space=Space(self.n);self.selected=None
    def remember(self,m):
        self.cache[m]=None;self.cache.move_to_end(m)
        if self.label is not None:
            self.labels[self.label]=m;self.labels.move_to_end(self.label)
        while len(self.cache)>self.capacity:
            old,_=self.cache.popitem(last=False)
            for k in list(self.labels):
                if self.labels[k]==old:del self.labels[k]
        while len(self.labels)>self.capacity*2:self.labels.popitem(last=False)
    def candidates(self):
        return [m for m in self.cache if all(apply(x,*m)==y for x,y in self.pairs)]
    def probe(self,pool):
        need(bool(pool),'empty probe pool')
        if self.policy not in ('active','cautious','active-reset'):return pool[0]
        ms=[] if self.policy=='active-reset' else self.candidates()
        def key(x):
            counts=Counter(apply(x,*m) for m in ms);n=len(ms)
            entropy=-sum(k/n*log2(k/n) for k in counts.values()) if n else 0
            # Search the unrestricted space as well as separating known models.
            return (entropy+self.space.query_score(x), x)
        return max(pool,key=key)
    def observe(self,x,y):
        x,y=vector(x,self.n),vector(y,self.n)
        if self.policy=='static' and self.space.unique_map() is not None:return
        if self.selected is not None and apply(x,*self.selected)!=y:
            self.stats['recall_conflicts']+=1;self.selected=None
            if self.policy=='label':self.labels.pop(self.label,None)
        pairs=(self.pairs+[(x,y)])[-(4 if self.policy=='window' else 16):]
        new=Space(self.n,pairs)
        if not new.count():
            self.stats['contradictions']+=1;pairs=[(x,y)];new=Space(self.n,pairs)
        self.pairs=pairs;self.space=new
        m=new.unique_map()
        if m is not None:self.remember(m)
    def predict(self,x):
        x=vector(x,self.n)
        if self.policy=='label' and self.label in self.labels:
            m=self.labels[self.label];self.selected=m;return apply(x,*m),'label-assumption'
        y=self.space.predict(x)
        if y is not None:return y,'stationary-consensus'
        if self.policy in ('recall','active','cautious'):
            ms=self.candidates();minimum=2 if self.policy=='cautious' else 1
            if len({p[0] for p in self.pairs})>=minimum and len(ms)==1:
                self.selected=ms[0];return apply(x,*ms[0]),'provisional-recall'
        return None,'abstain'
