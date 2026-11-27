import json,random,collections
from anticipation import Anticipation,Rates,POLICIES
from analogy import apply
N=16;T=120;WIDTH=10
REGIMES=('stable','return','warning','misleading','hidden','near','novel')
def fixture(seed,regime):
 r=random.Random(seed)
 def vec():return tuple(r.randrange(3) for _ in range(N))
 def mapping():return tuple(r.sample(range(N),N)),r.randrange(2)
 maps=[mapping() for _ in range(4)]
 if regime=='near':
  a,f=maps[0];maps=[(a,f)]
  for j in range(3):
   b=list(a);b[2*j],b[2*j+1]=b[2*j+1],b[2*j];maps.append((tuple(b),f))
 boot=[(x,apply(x,*maps[0])) for x in [vec() for _ in range(8)]];m=maps[0];k=0;steps=[]
 # Fixed randomized schedule, not aligned with verification accounting windows.
 switches=set(r.sample(range(4,T-3),12));cues={t for t in range(T) if r.random()<.08}
 if regime in ('warning','near','prewarning','lagwarning'):
  shift=-1 if regime=='prewarning' else 1 if regime=='lagwarning' else 0
  cues|={t+shift for t in switches if r.random()<.85}
 if regime=='misleading':cues|={t for t in range(T) if r.random()<.25}
 for t in range(T):
  changed=t in switches and regime!='stable'
  if changed:k=(k+1)%4;m=mapping() if regime=='novel' else maps[k]
  label=str(k) if regime=='return' else 'same'
  pool=[(x,apply(x,*m)) for x in [vec() for _ in range(8)]];qs=[(x,apply(x,*m)) for x in [vec() for _ in range(3)]]
  steps.append((label,t in cues,pool,qs,changed))
 return boot,steps

def run(fx,policy,seed,budget=3,rates=None,fit=None,trace=False):
 boot,steps=fx;g=Anticipation(N,policy,WIDTH,budget,rates,seed);g.boot(boot,steps[0][0]);out={str(a):collections.Counter() for a in (None,0,1,2,4)};log=[]
 for t,(label,cue,pool,qs,changed) in enumerate(steps):
  take=g.step(label,cue)
  if take:
   age=g.age();x=g.probe([a for a,b in pool]);y=dict(pool)[x];p=g.observe(x,y)
   if fit is not None and p is not None:fit.add(cue,age,p!=y)
  for x,y in qs:
   p,basis=g.predict(x)
   for a,s in out.items():
    pred=p if a=='None' or g.last is not None and g.age()<=int(a) else None
    status='abstain' if pred is None else 'correct' if pred==y else 'wrong';s[status]+=1
   if trace:log.append((t,take,g.age(),p,basis))
 return {'gates':{k:dict(v) for k,v in out.items()},'stats':dict(g.stats)},log

def main():
 rates=Rates()
 for regime in REGIMES:
  for seed in range(41001,41005):run(fixture(seed,regime),'periodic',seed,fit=rates)
 rows=[]
 for cohort,start in [('main',41101),('fresh',41201)]:
  for regime in REGIMES:
   for seed in range(start,start+6):
    fx=fixture(seed,regime)
    for budget in (3,5):
     for p in POLICIES[:5]:
      s,_=run(fx,p,seed,budget,rates);rows.append(dict(cohort=cohort,regime=regime,seed=seed,budget=budget,policy=p,**s))
   print(cohort,regime,flush=True)
 with open('results.json','w') as f:json.dump({'rates':rates.report(),'rows':rows},f,indent=2)
if __name__=='__main__':main()
