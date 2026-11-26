"""ADAPTATION 028: deterministic local simulation, no live writes."""
import random,json,time
from collections import Counter
import circulation as c
import interdependence as d
N=6; TICKS=48; BUDGET=6500; CAP=32000
POLICIES=('static','reactive','durable','adaptive')
def fixture(seed,regime):
 r=random.Random(seed);obj={};born={};initial=[set() for _ in range(N)];records=[];parity={};events=[]
 def create(t):
  b=r.randbytes(r.choice((384,768,1536,3072)));h=c.digest(b);obj[h]=b;born[h]=t;return h
 for i in range(24):initial[i%N].add(create(0))
 for g in range(6):
  ps=(g,(g+1)%N,(g+2)%N);hs=[sorted(initial[p])[g//2] for p in ps];rec,b=d.equation(obj,dict.fromkeys(hs,1));records.append(rec);parity[rec['parity']]=b
 for g,rec in enumerate(records):initial[(g+3)%N].add(rec['parity'])
 down=[0]*N
 for t in range(TICKS):
  down=[max(0,x-1) for x in down];wipe=[]
  if t:
   for p in range(N):
    if r.random()<(.17 if regime=='transient' else .07):down[p]=max(down[p],r.randint(1,3))
    if regime!='transient' and r.random()<(.045 if regime=='attrition' else .014):wipe.append(p);down[p]=max(down[p],2)
   if regime=='correlated' and r.random()<.13:
    a=2*r.randrange(3)
    for p in (a,a+1):down[p]=max(down[p],r.randint(2,4))
    if r.random()<.48:wipe.extend((a,a+1))
  online=[p for p in range(N) if not down[p]];arrivals=[]
  if t and t%6==0 and online:
   for _ in range(2):arrivals.append((r.choice(online),create(t)))
  events.append((online,sorted(set(wipe)),arrivals))
 return obj,born,initial,records,parity,events

def available(refs,stores,peers,records,obj,parity):
 present=set().union(*(stores[p] for p in peers));known={h:obj[h] for h in refs&present};ps={h:parity[h] for h in present&parity.keys()}
 return d.solve(refs,records,known,ps)

def simulate(fx,policy,trace=False,lifetime=None,retire=False):
 obj,born,initial,records,parity,events=fx;costs={h:len(c.object_encode(b))+32 for h,b in (obj|parity).items()};stores=[set(x) for x in initial];last=[set(x) for x in initial];refs={h for h,t in born.items() if t==0};streak=[0]*N;wipes=[0]*N;stat=Counter();lost=set();rows=[];prev=set(range(N));pending=Counter();initial_cost=sum(costs[h] for a in stores for h in a)
 for t,(online,wipe,arrivals) in enumerate(events):
  online=set(online);stat['offline_peer_ticks']+=N-len(online)
  for p in wipe:stores[p].clear()
  for p,h in arrivals:stores[p].add(h);refs.add(h)
  for p in range(N):
   streak[p]=0 if p in online else streak[p]+1
   if p in online:
    if last[p]-stores[p]:wipes[p]+=1
    last[p]=set(stores[p])
  for p in online-prev:
   for h in stores[p]:stat['returned_copy_after_repair']+=pending.pop((p,h),0)
   for key in list(pending):
    if key[0]==p:del pending[key]
  pre=available(refs,stores,online,records,obj,parity);stat['pre_missing_ticks']+=len(refs-pre.keys());direct=set().union(*(stores[p] for p in online));spent=0;actions=[]
  while policy in POLICIES:
   sizes=[sum(costs[h] for h in a) for a in stores];best=None
   for h in sorted(refs):
    if h not in pre:continue
    active=[p for p in online if h in stores[p]];ads=[p for p in range(N) if h in last[p]];domains={p//2 for p in ads};live={p//2 for p in active}
    if policy=='static':want=t-born[h]<4 and len(ads)<2
    elif policy=='reactive':want=len(active)<2
    elif policy=='durable':want=len(domains)<2 or not active
    else:
     credible=[p for p in ads if p in online or (streak[p]<4 and wipes[p]==0)]
     want=len({p//2 for p in credible})<2 or not active or (len(active)<2 and any(streak[p]>=4 for p in ads))
    if not want:continue
    gather=0;recipe=None
    if not active:
     for rec in records:
      hs={a[0] for a in rec['members']};ph=rec['parity']
      if h in hs and ph in direct and hs-{h}<=direct:
       price=sum(costs[k] for k in (hs-{h})|{ph})
       if recipe is None or price<gather:gather=price;recipe=rec
     if recipe is None:continue
    price=costs[h]+gather
    if spent+price>BUDGET or (lifetime is not None and stat['wire_bytes']+spent+price>lifetime):continue
    for p in sorted(online):
     if h in stores[p] or sizes[p]+costs[h]>CAP:continue
     if policy=='reactive':score=(not active,len(active)<2,p//2 not in live,-price,-sizes[p],-p,h)
     else:score=(not active,len(domains)<2,p//2 not in domains,-price,-wipes[p],-sizes[p],-p,h)
     if best is None or score>best[0]:best=(score,h,p,price,recipe)
   if best is None:break
   _,h,p,price,recipe=best
   if recipe:
    hs={a[0] for a in recipe['members']};b=d.solve(hs,[recipe],{k:obj[k] for k in hs-{h}},{recipe['parity']:parity[recipe['parity']]})[h];stat['regenerated_repairs']+=1
   else:b=pre[h]
   if c.digest(b)!=h or b!=obj[h]:raise RuntimeError('bad repair')
   for q in range(N):
    if q not in online and h in last[q]:pending[q,h]+=1
   stores[p].add(h);last[p].add(h);direct.add(h);spent+=price;stat['repairs']+=1;actions.append((p,h,price))
  if retire:
   # Only retire an online direct copy when two verified live domains remain.
   # This protects against any one additional domain loss at this instant, not future correlated failures.
   for p in sorted(online,key=lambda p:-sum(costs[h] for h in stores[p])):
    for h in sorted(stores[p]&refs,key=lambda h:(-costs[h],h)):
     if sum(costs[k] for k in stores[p])<CAP*.75:break
     others=[q for q in online if q!=p and h in stores[q]]
     if len({q//2 for q in others})<2:continue
     if any(c.digest(obj[h])!=h for q in others):raise RuntimeError('bad retirement evidence')
     stores[p].remove(h);last[p].remove(h);stat['retired_copies']+=1;stat['retired_bytes']+=costs[h]
  post=available(refs,stores,online,records,obj,parity);durable=available(refs,stores,range(N),records,obj,parity)
  missing=refs-post.keys();forever=refs-durable.keys();lost|=forever
  stat['missing_ticks']+=len(missing);stat['permanent_missing_ticks']+=len(forever);stat['wire_bytes']+=spent;stat['complete_ticks']+=not missing;stat['object_ticks']+=len(refs)
  stat['domain_vulnerable_ticks']+=sum(len({p//2 for p in range(N) if h in stores[p]})<2 for h in refs)
  stat['peak_storage']=max(stat['peak_storage'],sum(costs[h] for a in stores for h in a));stat['max_tick_wire']=max(stat['max_tick_wire'],spent)
  if trace:rows.append(dict(tick=t,online=sorted(online),wipe=wipe,arrivals=arrivals,actions=actions,missing=sorted(missing),permanent=sorted(forever),stores=[sorted(a) for a in stores]))
  prev=online
 stat.update(permanent_objects=len(lost),final_objects=len(refs),initial_storage=initial_cost,final_storage=sum(costs[h] for a in stores for h in a))
 return dict(stat),rows
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--seeds',type=int,default=8);p.add_argument('--start',type=int,default=2801);p.add_argument('--output',default='results.json');a=p.parse_args();rows=[];start=time.perf_counter()
 for regime in ('transient','attrition','correlated'):
  for seed in range(a.start,a.start+a.seeds):
   fx=fixture(seed,regime)
   for policy in POLICIES:
    stats,_=simulate(fx,policy);rows.append(dict(regime=regime,seed=seed,policy=policy,**stats))
  print(regime,round(time.perf_counter()-start,2),flush=True)
 with open(a.output,'w') as f:json.dump(rows,f,indent=2)
