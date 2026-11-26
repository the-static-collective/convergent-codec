"""DC1: bounded counterexample-directed observation after a CU1 singleton."""
import argparse, json, random, math
import circulation as c
from curiosity import Inquiry
POLICIES=('rotation','random','fault','challenge','protected','expanded','balanced')

def alternatives(q, lead):
    """Hypothetical near misses; not asserted causes or calibrated probabilities."""
    base=q.models[lead]; families={k:set() for k in ('addition','omission','local')}
    def add(f,delta):
        diff=frozenset(k for k in set(base)|set(delta) if base.get(k,q.base[k])!=delta.get(k,q.base[k]))
        if diff and not diff.intersection(q.observed):families[f].add(diff)
    for other in q.models.values():
        if all(base.get(k,v)==v for k,v in other.items()):add('addition',base|other)
        add('omission',{k:v for k,v in base.items() if k not in other})
    for k,v in q.base.items():
        if v=='verified' and k not in q.observed:families['local'].add(frozenset((k,)))
    return families

def select(q,n,policy='protected',seed=0):
    c.need(policy in POLICIES and 0<=n<=len(q.refs),'selection bounds')
    pool=[h for h in q.refs if any((p,h) not in q.observed for p in q.live)]
    n=min(n,len(pool));ms=q.compatible();rng=random.Random(seed);tie={h:rng.random() for h in pool}
    if q.conflicts or len(ms)!=1:return q.select(n,'curiosity',seed)
    lead=ms[0]
    if policy=='rotation':return pool[:n]
    if policy=='random':return sorted(rng.sample(pool,n))
    if policy=='fault':return sorted(sorted(pool,key=lambda h:(-sum(q.predict(lead,(p,h))!='verified' and q.base[p,h]=='verified' for p in q.live if (p,h) not in q.observed),tie[h]))[:n])
    fs=alternatives(q,lead);weights={};hits={h:set() for h in pool}
    for f,ds in fs.items():
        for i,d in enumerate(sorted(ds,key=lambda x:sorted(x))):
            key=(f,i);weights[key]=1/len(ds)
            for p,h in d:
                if p in q.live and h in hits:hits[h].add(key)
    chosen=pool[:(n+1)//2] if policy=='protected' else []
    if policy=='balanced' and n:
        # Reserve one slot for a possible exception inside the predicted fault region.
        inside=[h for h in pool if any((p,h) in q.models[lead] and (p,h) not in q.observed for p in q.live)]
        if inside:chosen=[max(inside,key=lambda h:(sum((p,h) in q.models[lead] for p in q.live if (p,h) not in q.observed),tie[h]))]
    covered=set().union(*(hits[h] for h in chosen))
    while len(chosen)<n:
        def score(h):
            new=hits[h]-covered
            if policy=='expanded':
                # Uniform count comparator on same expanded challenge pool; binary entropy.
                p=len(new)/(len(weights)+1);v=-(p*math.log2(p)+(1-p)*math.log2(1-p)) if 0<p<1 else 0
            else:v=sum(weights[k] for k in sorted(new))
            return v,tie[h]
        h=max((h for h in pool if h not in chosen),key=score);chosen.append(h);covered.update(hits[h])
    return sorted(chosen)

def receipt(q,n,policy,seed):
    ms=q.compatible();fs=alternatives(q,ms[0]) if len(ms)==1 and not q.conflicts else {}
    return {'schema':'PN1','manifest_pin':q.pin,'diagnostic_schema':'DC1','evidence':q.summary(),'challenge_families':{f:len(ds) for f,ds in fs.items()},'next_selection':select(q,n,policy,seed),'qualification':'Finite challenge vocabulary; surviving tests do not prove the explanation.'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('baseline');p.add_argument('groups');p.add_argument('reports',nargs='+');p.add_argument('--sample',type=int,default=4);p.add_argument('--policy',choices=POLICIES,default='protected');p.add_argument('--seed',type=int,default=0);a=p.parse_args()
    load=lambda p:json.loads(c.read_limited(p,64*1024*1024))
    q=Inquiry(load(a.baseline),load(a.groups))
    for f in a.reports:q.update(load(f))
    print(json.dumps(receipt(q,min(a.sample,len(q.refs)),a.policy,a.seed),indent=2))
if __name__=='__main__':main()
