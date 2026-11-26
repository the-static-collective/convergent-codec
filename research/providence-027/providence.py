"""Rank-aware local preservation planner, using ID1 recovery."""
import random
import circulation as c
import interdependence as d

def candidates(obj,base,seed):
    rng=random.Random(seed); owner={h:i for i,a in enumerate(base) for h in a}; out=[]
    for h,b in sorted(obj.items()):
        for p in range(len(base)):
            if p!=owner[h]:out.append((p,((h,1),),None,b,len(c.object_encode(b)),h))
    qs=[sorted(a,key=lambda h:(len(obj[h]),h)) for a in base];groups=set()
    for width in (2,3,4):
        for offset in (0,1):
            q=[a[offset:]+a[:offset] for a in qs]
            while True:
                ids=sorted((i for i,a in enumerate(q) if a),key=lambda i:(-len(q[i]),i))[:width]
                if len(ids)<2:break
                groups.add(tuple(sorted(q[i].pop(0) for i in ids)))
    for _ in range(12):
        ids=rng.sample([i for i,q in enumerate(qs) if q],rng.choice((2,3,4)));groups.add(tuple(sorted(rng.choice(qs[i]) for i in ids)))
    for hs in sorted(groups):
        for co in (dict.fromkeys(hs,1),dict(zip(hs,range(1,len(hs)+1)))):
            r,b=d.equation(obj,co);cost=len(c.object_encode(b))+len(c.canon(r))+1
            for p in range(len(base)):
                if p not in {owner[h] for h in hs}:out.append((p,tuple(co.items()),r,b,cost,r['parity']))
    return out

def state(obj,base,chosen,loss):
    known=set().union(*(a for i,a in enumerate(base) if i not in loss));unknown=sorted(set(obj)-known);idx={h:i for i,h in enumerate(unknown)};rows=[]
    for dest,terms,*_ in chosen:
        if dest in loss:continue
        v=[0]*len(idx)
        for h,k in terms:
            if h in idx:v[idx[h]]=k
        rows.append((v,b''))
    return idx,{j:r for j,(r,_) in d.reduce_rows(rows,len(idx)).items()}

def gain(terms,idx,basis):
    v=[0]*len(idx)
    for h,k in terms:
        if h in idx:v[idx[h]]=k
    for j,p in sorted(basis.items()):
        k=v[j]
        if k:v=[x^d.TABLE[k][y] for x,y in zip(v,p)]
    j=next((i for i,x in enumerate(v) if x),None)
    if j is None:return 0,0
    v=[d.TABLE[d.INV[v[j]]][x] for x in v];delta=int(sum(bool(x) for x in v)==1)
    for p in basis.values():
        k=p[j]
        if k:delta+=int(sum(bool(x^d.TABLE[k][y]) for x,y in zip(p,v))==1)-int(sum(bool(x) for x in p)==1)
    return delta,1

def plan(obj,base,pool,budget,scenarios,rank_bonus=.25):
    chosen=[];spent=probes=0;used=set();has_records=False
    while True:
        ss=[(set(loss),weight,*state(obj,base,chosen,loss)) for loss,weight in scenarios];best=None
        for a in pool:
            dest,terms,r,b,price,h=a;cost=price+int(r is not None and not has_records)
            if spent+cost>budget or (dest,h) in used:continue
            value=0
            for loss,w,idx,bs in ss:
                if dest not in loss:
                    u,k=gain(terms,idx,bs);value+=w*(u+rank_bonus*k)
            probes+=1
            if value<=0:continue
            key=(value/cost,value,-cost,h,-dest)
            if best is None or key>best[0]:best=(key,a,cost)
        if best is None:break
        _,a,cost=best;chosen.append(a);spent+=cost;used.add((a[0],a[5]));has_records|=a[2] is not None
    inv=[set(x) for x in base];rs=[];payload={};seen=set()
    for dest,terms,r,b,cost,h in chosen:
        inv[dest].add(h)
        if r is not None:
            if h not in seen:rs.append(r);seen.add(h)
            payload[h]=b
    return inv,rs,payload,spent,{'copies':sum(a[2] is None for a in chosen),'equations':len(rs),'probes':probes,'pool':len(pool)}
