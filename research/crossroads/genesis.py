"""Genesis: staged compositional search with exact self-contained expression frames.
No target labels passed to search. Target functions and environments are synthetic.
"""
import living as L
import json,random,hashlib,zlib,itertools,statistics,time
from pathlib import Path
ROOT=Path(__file__).parent
ATOMS=tuple(L.ATOMS)
NAME={L.name(e):e for e in ATOMS}
# Prefix bytecode: 0..22 atom indices, 240 add, 241 subtract, 242 multiply.
OPS=(240,241,242)
def atom(e):return bytes([ATOMS.index(e)])
def expr(op,a,b):
    if op!=241 and a>b:a,b=b,a
    return bytes([op])+a+b

def parse(e,p=0,depth=0):
    if depth>4 or p>=len(e):raise ValueError('expression bounds')
    k=e[p];p+=1
    if k<len(ATOMS):return (k,),p
    if k not in OPS:raise ValueError('opcode')
    a,p=parse(e,p,depth+1);b,p=parse(e,p,depth+1);return (k,a,b),p

def pretty(e):
    def rec(t):return L.name(ATOMS[t[0]]) if len(t)==1 else '('+rec(t[1])+{240:' + ',241:' - ',242:' * '}[t[0]]+rec(t[2])+')'
    t,p=parse(e);assert p==len(e);return rec(t)

def evaluate(e,x):
    def rec(t):
        if len(t)==1:return L.vm(ATOMS[t[0]],x)
        a,b=rec(t[1]),rec(t[2]);return a+b if t[0]==240 else a-b if t[0]==241 else a*b
    t,p=parse(e)
    if p!=len(e):raise ValueError('trailing expression')
    return rec(t)

def pool(roots,parents=()):
    roots=set(roots);out=set(roots)
    for a in roots|set(parents):
        for b in roots:
            for op in OPS:
                out.add(expr(op,a,b))
                if op==241:out.add(expr(op,b,a))
    return sorted(out,key=lambda e:(len(e),e))

def bank(seed,n):
    rng=random.Random(seed);return [[rng.randint(-5,8) for _ in range(rng.randint(2,9))] for i in range(n)]
def signsum(x):return sum((v>0)-(v<0) for v in x)
# Frozen task set: first stage compound discovery, second stage novel compositions,
# negative controls not generally expressible by this grammar.
STAGE1={'span':lambda x:max(x)-min(x),'energy_plus_mass':lambda x:sum(v*v for v in x)+sum(x),'endpoint_product':lambda x:x[0]*x[-1], 'mass_times_peak':lambda x:sum(x)*max(x),'signed_balance':lambda x:sum(x)-signsum(x)}
STAGE2={'span_times_mass':lambda x:(max(x)-min(x))*sum(x),'energy_mass_times_first':lambda x:(sum(v*v for v in x)+sum(x))*x[0], 'endpoint_product_plus_peak':lambda x:x[0]*x[-1]+max(x),'mass_peak_minus_sign':lambda x:sum(x)*max(x)-signsum(x),'balance_times_last':lambda x:(sum(x)-signsum(x))*x[-1], 'unrelated_index_weighted':lambda x:sum((i+1)*v for i,v in enumerate(x)), 'unrelated_distinct':lambda x:len(set(x)), 'unrelated_median_twice':lambda x:int(2*statistics.median(x))}
# Frame stores no hidden dictionary. Inline prefix expression; every value and context digest counted.
def wire(xs,ys,e=None):
    r=L.raw([ys]);h=b'GE1'+L.u(len(xs))+L.input_hash(xs);d=hashlib.sha256(r).digest()
    opts=[h+b'R'+r+d,h+b'Z'+zlib.compress(r,9)+d]
    if e is not None:
        rr=[y-evaluate(e,x) for x,y in zip(xs,ys)];p=L.u(len(e))+e+L.residual(rr)
        opts += [h+b'M'+p+d,h+b'H'+zlib.compress(p,9)+d]
    return min(opts,key=lambda b:(len(b),b))
def decode(f,xs):
    r=L.Reader(f[:-32]);assert r.take(3)==b'GE1';n=r.u();assert n==len(xs) and r.take(32)==L.input_hash(xs);mode=r.take(1);p=r.take(len(r.b)-r.p)
    if mode in (b'Z',b'H'):p=zlib.decompress(p)
    r=L.Reader(p)
    if mode in (b'R',b'Z'):y=[r.s() for _ in xs]
    elif mode in (b'M',b'H'):
        e=r.take(r.u());v=[evaluate(e,x) for x in xs];tag=r.take(1);rr=[0]*n
        if tag==b'\0':rr=[r.s() for _ in xs]
        elif tag==b'\1':
            last=-1
            for i in range(r.u()):
                j,a=r.u(),r.s();assert last<j<n and a;rr[j]=a;last=j
        else:raise ValueError('residual')
        y=[a+b for a,b in zip(v,rr)]
    else:raise ValueError('mode')
    r.done()
    if hashlib.sha256(L.raw([y])).digest()!=f[-32:]:raise ValueError('digest')
    return y

def search(xs,targets,candidates,budget=None):
    # Candidate expressions evaluated once over common calibration bank; count vector evaluations,
    # and scalar output comparisons separately. Select by actual emitted residual bytes (raw fallback separately).
    best={k:None for k in targets};hits={};count=0
    for e in candidates[:budget]:
        v=[evaluate(e,x) for x in xs];count+=1
        for k,y in targets.items():
            rr=[a-b for a,b in zip(y,v)];cost=len(L.u(len(e)))+len(e)+len(L.residual(rr));score=(cost,len(e),e)
            if best[k] is None or score<best[k]:best[k]=score
            if not any(rr) and k not in hits:hits[k]=count
    return {k:v[2] for k,v in best.items()},hits,count

def run(seed,roots,label,cal1,cal2,test,budget,inherit_parents=True,priority=False):
    y1={k:[f(x) for x in cal1] for k,f in STAGE1.items()};y2={k:[f(x) for x in cal2] for k,f in STAGE2.items()}
    p1=pool(roots);b1,h1,n1=search(cal1,y1,p1,budget)
    # Promote only exact calibration expressions which reduce actual wire cost compared with literal or zlib.
    parents=sorted({e for k,e in b1.items() if k in h1 and len(e)>1 and len(wire(cal1,y1[k],e))<len(wire(cal1,y1[k]))})
    p2=pool(roots,parents if inherit_parents else ())
    if priority:
        parentset=set(parents)-set(roots);preferred=set()
        for a in parentset:
            for b in roots:
                for op in OPS:
                    preferred.add(expr(op,a,b))
                    if op==241:preferred.add(expr(op,b,a))
        p2=sorted(p2,key=lambda e:(e not in preferred,len(e),e))
    b2,h2,n2=search(cal2,y2,p2,budget)
    result={};frames={}
    for k,f in STAGE2.items():
        y=[f(x) for x in test];e=b2[k];pred=[evaluate(e,x) for x in test];fr=wire(test,y,e);base=wire(test,y)
        assert decode(fr,test)==y and decode(base,test)==y
        try:decode(fr[:-1]+bytes([fr[-1]^1]),test)
        except ValueError:pass
        else:raise AssertionError('tamper')
        result[k]={'expression':pretty(e),'expression_hex':e.hex(),'bytes':len(fr),'baseline_bytes':len(base),'matches':sum(a==b for a,b in zip(pred,y)),'total':len(y),'first_exact_calibration_candidate':h2.get(k),'mode':chr(fr[4+32]) if len(test)<128 else 'see frame'}
        frames[k]=fr.hex()
    return {'arm':label,'roots':[pretty(e) for e in roots],'root_definition_bytes':sum(map(len,roots)),'parents':[pretty(e) for e in parents],'parent_definition_bytes':sum(map(len,parents)),'stage1_pool':len(p1),'stage2_pool':len(p2),'stage1_evals':n1,'stage2_evals':n2,'first_stage_exact':len(h1),'stage1_hits':h1,'stage2_hits':h2,'candidate_target_comparisons':n1*len(y1)+n2*len(y2),'bytes':sum(t['bytes'] for t in result.values()),'baseline_bytes':sum(t['baseline_bytes'] for t in result.values()),'exact_rows':sum(t['matches']==t['total'] for t in result.values()),'matches':sum(t['matches'] for t in result.values()),'total':sum(t['total'] for t in result.values()),'rows':result,'frames':frames}

def main():
    donors=json.loads((ROOT/'donor_summary.json').read_text())['domains'];inherited=sorted({atom(NAME[n]) if n in NAME else expr(241,atom(NAME['min(id)']),atom(NAME['max(id)'])) for d in donors.values() for n in d['alphabet']});allroots=[atom(e) for e in ATOMS];generic=[atom(NAME[n]) for n in ('length','first','last','sum(id)','sum(square)','min(id)','max(id)','sum(sign)')];generic+= [expr(241,atom(NAME['max(id)']),atom(NAME['min(id)']))]
    # Same grammar; inherited compound is supplied as a seed, charged separately. Cold must discover it.
    runs=[]
    for seed in (808,809,810,811):
        c1,c2,t=bank(seed,24),bank(seed+1000,24),bank(seed+2000,64);rng=random.Random(seed)
        arms=[('inherited',inherited,None),('inherited_bounded',inherited,200),('cold_full',allroots,None),('cold_bounded',allroots,200),('fixed_statistical',generic,None),('random_matched',sorted(rng.sample(allroots,len(inherited))),None),('inherited_no_parents',inherited,None),('inherited_sign_closed',sorted(set(inherited)|{expr(241,atom(NAME['max(id)']),atom(NAME['min(id)']))}),None),('inherited_prioritized',inherited,200),('fixed_prioritized',generic,200),('cold_prioritized',allroots,200),('sign_closed_prioritized',sorted(set(inherited)|{expr(241,atom(NAME['max(id)']),atom(NAME['min(id)']))}),200)]
        # donor selection is frozen, not optimized on target results
        for label,roots,budget in arms:
            r=run(seed,roots,label,c1,c2,t,budget,inherit_parents=label!='inherited_no_parents',priority=label.endswith('prioritized'));r.update(seed=seed,budget=budget);runs.append(r);print(seed,label,r['stage1_evals']+r['stage2_evals'],r['exact_rows'],r['bytes'],flush=True)
    (ROOT/'results.json').write_text(json.dumps({'runs':runs,'inputs':{str(s):{'cal1':bank(s,24),'cal2':bank(s+1000,24),'test':bank(s+2000,64)} for s in (808,809,810,811)},'donor_source':'CROSSROADS 007 summary, not retrained','donor_calibration_bytes':{n:d['calibration_bytes'] for n,d in donors.items()}},indent=2,sort_keys=True))
if __name__=='__main__':main()
