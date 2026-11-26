"""JB1: separate historical gifts from expiring allocation scores; no debts created."""
from collections import deque
from reciprocity import verify,need
MODES=('gift','permanent','reset','sliding','decay','voluntary')
class Memory:
    def __init__(self,n,mode='sliding',period=8):
        need(mode in MODES and 1<=n<=32 and 1<=period<=64,'bounds')
        self.n=n;self.mode=mode;self.period=period;self.t=-1
        self.events=deque();self.score=[[0]*n for _ in range(n)]
        self.lifetime=[[0]*n for _ in range(n)];self.releases=0
    def step(self,t,releases=()):
        need(t==self.t+1,'round order');self.t=t
        if self.mode=='reset' and t%self.period==0:self.score=[[0]*self.n for _ in range(self.n)]
        if self.mode in ('sliding','decay'):
            while self.events and t-self.events[0][0]>=self.period:self.events.popleft()
            self.score=[[0]*self.n for _ in range(self.n)]
            for born,i,j in self.events:self.score[i][j]+=self.period if self.mode=='sliding' else self.period-(t-born)
        if self.mode=='voluntary':
            for i,j in releases:
                need(0<=i<self.n and 0<=j<self.n and i!=j,'release scope')
                # Release only giver i's positive net allocation score against j.
                amount=max(0,self.score[i][j]-self.score[j][i]);self.score[i][j]-=amount;self.releases+=amount
    def allocate(self,offers,claims,evidence=None):
        need(self.t>=0 and len(offers)==len(claims)==self.n,'field')
        limit=list(claims) if evidence is None else [min(a,b) for a,b in zip(claims,evidence)]
        need(len(limit)==self.n and all(type(x) is int and x>=0 for x in limit),'claims')
        supply=[min(o.cap,max(0,o.stock-o.floor)) for o in offers];sent=[0]*self.n;recv=[0]*self.n;out=[]
        h=[row[:] for row in self.score];scale=self.period if self.mode in ('sliding','decay') else 1
        while True:
            choices=[]
            for i,o in enumerate(offers):
                if sent[i]>=supply[i]:continue
                for j in sorted(set(o.recipients)):
                    if i==j or recv[j]>=limit[j]:continue
                    if self.mode!='gift' and h[i][j]-h[j][i]>=2*scale:continue
                    choices.append(((recv[j]/limit[j],-(limit[j]-recv[j]),-(supply[i]-sent[i]),j,i),i,j))
            if not choices:break
            _,i,j=min(choices);out.append((i,j));sent[i]+=1;recv[j]+=1;h[i][j]+=scale
        verify(offers,claims,out);return tuple(out)
    def record(self,actions):
        scale=self.period if self.mode in ('sliding','decay') else 1
        for i,j in actions:
            need(0<=i<self.n and 0<=j<self.n and i!=j,'gift scope')
            self.lifetime[i][j]+=1;self.score[i][j]+=scale
            if self.mode in ('sliding','decay'):self.events.append((self.t,i,j))
