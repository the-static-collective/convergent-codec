"""CROSSROADS 009: exact catalog conservation and symbolic candidate quotient.
Standard-library only. All proofs are formal integer-ring identities over opaque atoms.
Source catalog is extracted from CROSSROADS 008, not retrained.
"""
import genesis as G
import living as L
import json,hashlib,zlib,collections,itertools,functools,random,statistics
from pathlib import Path
P=Path(__file__).parent

def sha(b):return hashlib.sha256(b).digest()
@functools.lru_cache(None)
def poly(e):
    t,p=G.parse(e)
    if p!=len(e):raise ValueError('expression trailing')
    def rec(t):
        if len(t)==1:return {(t[0],):1}
        a,b=rec(t[1]),rec(t[2]);c=collections.Counter()
        if t[0]==242:
            for x,i in a.items():
                for y,j in b.items():c[tuple(sorted(x+y))]+=i*j
        else:
            c.update(a)
            for y,j in b.items():c[y]+=j if t[0]==240 else -j
        return {k:v for k,v in c.items() if v}
    return tuple(sorted(rec(t).items()))

def quotient(es):
    best={}
    for e in sorted(set(es),key=lambda e:(len(e),e)):best.setdefault(poly(e),e)
    return sorted(best.values(),key=lambda e:(len(e),e))

def split(e):
    if len(e)==1:return None
    _,p=G.parse(e,1);return e[0],e[1:p],e[p:]

def raw_catalog(es):return L.u(len(es))+b''.join(L.u(len(e))+e for e in es)

def read_raw(p):
    r=L.Reader(p);es=[r.take(r.u()) for _ in range(r.u())];r.done()
    for e in es:poly(e)
    return es

def dag_payload(es):
    # Exact original ordered catalog; atom IDs are implicit VM context.
    nodes=[];ids={bytes([i]):i for i in range(len(G.ATOMS))}
    def add(e):
        if e not in ids:
            op,a,b=split(e);i,j=add(a),add(b);ids[e]=len(G.ATOMS)+len(nodes);nodes.append((op,i,j))
        return ids[e]
    roots=[add(e) for e in es]
    return L.u(len(nodes))+b''.join(bytes([op])+L.u(a)+L.u(b) for op,a,b in nodes)+L.u(len(roots))+b''.join(L.u(i) for i in roots)

def read_dag(p):
    r=L.Reader(p);nodes=[bytes([i]) for i in range(len(G.ATOMS))]
    n=r.u()
    if n>10000:raise ValueError('node limit')
    for _ in range(n):
        op=r.take(1)[0];a,b=r.u(),r.u()
        if op not in G.OPS or max(a,b)>=len(nodes):raise ValueError('bad edge')
        e=bytes([op])+nodes[a]+nodes[b];poly(e);nodes.append(e)
    ids=[r.u() for _ in range(r.u())];r.done();return [nodes[i] for i in ids]

def frames(es):
    raw=raw_catalog(es);dag=dag_payload(es);d=sha(raw)
    out={k:b'CK1'+k.encode()+p+d for k,p in [('R',raw),('Z',zlib.compress(raw,9)),('D',dag),('H',zlib.compress(dag,9))]}
    for f in out.values():assert decode(f)==es
    return out

def decode(f):
    if f[:3]!=b'CK1':raise ValueError('header')
    k=f[3:4];p=f[4:-32]
    if k in (b'Z',b'H'):p=zlib.decompress(p)
    if k not in (b'R',b'Z',b'D',b'H'):raise ValueError('mode')
    es=read_dag(p) if k in (b'D',b'H') else read_raw(p)
    if sha(raw_catalog(es))!=f[-32:]:raise ValueError('digest')
    return es

def catalog():
    return json.loads((P/'catalog.json').read_text())

def closure(roots,parents):return G.pool(roots,parents)

def search_compare(xs,targets,pool,hold):
    q=quotient(pool);a,ha,na=G.search(xs,targets,pool);b,hb,nb=G.search(xs,targets,q)
    assert a==b # cheapest canonical syntax representative wins ties in original search too
    rows={}
    for k,e in a.items():
        y=hold[k];f=G.wire(hold['inputs'],y,e);assert G.decode(f,hold['inputs'])==y
        rows[k]={'expression':G.pretty(e),'exact':sum(G.evaluate(e,x)==v for x,v in zip(hold['inputs'],y)),'n':len(y),'bytes':len(f),'frame':f.hex()}
    return {'full':na,'quotient':nb,'rows':rows}

def main():
    c=catalog();es=[bytes.fromhex(e) for e in c['expressions']];q=quotient(es)
    fs=frames(es);compact=frames(q)
    for f in fs.values():
        try:decode(f[:-1]+bytes([f[-1]^1]))
        except ValueError:pass
        else:raise AssertionError('tamper')
    alias=[{'original':e.hex(),'representative':next(k.hex() for k in q if poly(k)==poly(e))} for e in es]
    # Proof witnesses are independently recomputable, not numeric coincidence.
    for a in alias:assert poly(bytes.fromhex(a['original']))==poly(bytes.fromhex(a['representative']))
    roots=[bytes.fromhex(e) for e in c['roots']];parents=[bytes.fromhex(e) for e in c['parents']];exact=[bytes.fromhex(e) for e in c['exact_stage2']]
    # Same acquired vocabulary, exact source syntax retained in catalog. No semantic merges based on sampled values.
    pool=closure(roots,parents+exact)
    # Stress test broader closure including all acquired expressions as potential parents.
    broad=closure(es,[]);bq=quotient(broad)
    # Counterfactual: remove compound parents without ability to restore them.
    atomic=[e for e in roots if len(e)==1]
    cold=closure(atomic,[])
    # Future targets constructed with earlier discovered expressions; three unrelated controls.
    targets={
     'third_generation_energy':lambda x:x[-1]*(x[0]*(sum(v*v for v in x)+sum(x))),
     'third_generation_span':lambda x:(sum(x)*(max(x)-min(x)))+x[0],
     'third_generation_balance':lambda x:(x[-1]*(sum(x)-sum((v>0)-(v<0) for v in x))) * max(x),
     'third_generation_peak':lambda x:(sum(x)*max(x)-sum((v>0)-(v<0) for v in x))+x[-1],
     'third_generation_endpoint':lambda x:(max(x)+x[0]*x[-1])*sum(x),
     'unrelated_weighted':lambda x:sum((i+1)*v for i,v in enumerate(x)),
     'unrelated_median':lambda x:int(2*statistics.median(x)),
     'unrelated_distinct':lambda x:len(set(x)),
    }
    runs=[]
    for seed in [909,910,911,912]:
        xs=G.bank(seed,24);ys={k:[fn(x) for x in xs] for k,fn in targets.items()};hold={'inputs':G.bank(seed+2000,64)};hold.update({k:[fn(x) for x in hold['inputs']] for k,fn in targets.items()})
        r=search_compare(xs,ys,pool,hold);r['seed']=seed
        cc,_,nn=G.search(xs,ys,cold);r['atomic_only']={'evaluations':nn,'rows':{k:sum(G.evaluate(e,x)==y for x,y in zip(hold['inputs'],hold[k])) for k,e in cc.items()}};runs.append(r)
    # Structural equivalence proof stress: every quotient group re-evaluated on fresh sequences.
    bank=G.bank(933,12);rep={poly(e):e for e in bq};checks=0
    for e in broad:
        if e==rep[poly(e)]:continue
        for x in bank:assert G.evaluate(e,x)==G.evaluate(rep[poly(e)],x);checks+=1
    result={'catalog_size':len(es),'semantic_classes':len(q),'catalog_frames':{k:len(v) for k,v in fs.items()},'semantic_only_frames':{k:len(v) for k,v in compact.items()},'aliases':alias,'catalog_frame_hex':{k:v.hex() for k,v in fs.items()},'semantic_frame_hex':{k:v.hex() for k,v in compact.items()},'broad_pool':len(broad),'broad_quotient':len(bq),'proof_spot_checks':checks,'future_runs':runs,'lineage_bytes':len((P/'catalog.json').read_bytes()),'notes':'Exact catalog frames conserve ordered bytecode list. Semantic-only frames do not conserve original syntax or source lineage. Atomic-only arm loses compound parent reuse, not a proof that unrestricted atomic closure cannot recover it.'}
    (P/'results.json').write_text(json.dumps(result,indent=2,sort_keys=True));print(json.dumps({k:v for k,v in result.items() if k not in ('aliases','catalog_frame_hex','semantic_frame_hex','future_runs')},indent=2))
    for r in runs:print(r['seed'],r['full'],r['quotient'],sum(v['exact']==v['n'] for v in r['rows'].values()),sum(v==64 for v in r['atomic_only']['rows'].values()),sum(v['bytes'] for v in r['rows'].values()))
if __name__=='__main__':main()
