"""CROSSROADS 005: executable expression alphabet, frozen transfer, exact frames."""
import hashlib, json, random, zlib, math, functools, operator, statistics
from pathlib import Path
# VM ISA: all candidates are available from the beginning; learning selects a dictionary.
MAPS=(('id',lambda x:x),('abs',abs),('square',lambda x:x*x),('sign',lambda x:(x>0)-(x<0)))
FOLDS=(('sum',sum),('prod',math.prod),('min',min),('max',max),('xor',lambda x:functools.reduce(operator.xor,x,0)))
# one-byte length, first, last; two-byte fold/map expression
BASE=[b'\x00']; POOL=[b'\x01',b'\x02']+[bytes([3+i,j]) for i in range(len(FOLDS)) for j in range(len(MAPS))]
ATOMS=tuple(BASE+POOL)
def name(e):
    if e[0]==8:return '('+name(ATOMS[e[1]])+' - '+name(ATOMS[e[2]])+')'
    return ['length','first','last'][e[0]] if e[0]<3 else FOLDS[e[0]-3][0]+'('+MAPS[e[1]][0]+')'
def vm(e,x):
    if e[0]==8:return vm(ATOMS[e[1]],x)-vm(ATOMS[e[2]],x)
    if e[0]<3:return (len(x),x[0],x[-1])[e[0]]
    return FOLDS[e[0]-3][1]([MAPS[e[1]][1](v) for v in x])
def u(n):
    if n<0:raise ValueError('negative unsigned')
    b=bytearray()
    while n>=128:b.append(128|(n&127));n>>=7
    b.append(n);return bytes(b)
def s(n):return u(2*n if n>=0 else -2*n-1)
class Reader:
    def __init__(self,b):self.b=b;self.p=0
    def take(self,n):
        if n<0 or self.p+n>len(self.b):raise ValueError('truncated')
        v=self.b[self.p:self.p+n];self.p+=n;return v
    def u(self):
        n=0
        for i in range(20):
            b=self.take(1)[0];n|=(b&127)<<(7*i)
            if b<128:
                if i and b==0:raise ValueError('noncanonical')
                return n
        raise ValueError('too long')
    def s(self):
        n=self.u();return n//2 if n%2==0 else -(n//2)-1
    def done(self):
        if self.p!=len(self.b):raise ValueError('trailing')
def raw(rows):return b''.join(s(v) for r in rows for v in r)
def input_hash(xs):return hashlib.sha256(json.dumps(xs,separators=(',',':')).encode()).digest()
def features(xs,es):return {e:[vm(e,x) for x in xs] for e in es}
def fits(xs,ys):
    # Generate affine candidates from a bounded prefix; score on full row for encoding.
    candidates={(0,ys[0]),(1,0),(-1,0)}
    for i in range(min(len(xs),8)):
        for j in range(i):
            d=xs[i]-xs[j]
            if d and (ys[i]-ys[j])%d==0:
                a=(ys[i]-ys[j])//d;b=ys[i]-a*xs[i]
                if abs(a)<=10000 and abs(b)<=10**12:candidates.add((a,b))
    return sorted(candidates)
def residual(r):
    dense=b'\x00'+b''.join(s(v) for v in r)
    pairs=[(i,v) for i,v in enumerate(r) if v]
    sparse=b'\x01'+u(len(pairs))+b''.join(u(i)+s(v) for i,v in pairs)
    return min((dense,sparse),key=lambda x:(len(x),x))
def records(rows,fs):
    result=[]
    for y in rows:
        row={}
        for e,x in fs.items():
            variants=[]
            for a,b in fits(x,y):
                r=[v-a*w-b for v,w in zip(y,x)]
                variants.append(s(a)+s(b)+residual(r))
            row[e]=min(variants,key=lambda v:(len(v),v))
        result.append(row)
    return result
def frame(rows,xs,mode,es=(),rec=None):
    r=raw(rows);h=b'LA1'+mode+u(len(rows))+u(len(xs))+input_hash(xs);digest=hashlib.sha256(r).digest()
    if mode==b'R':p=r
    elif mode==b'Z':p=zlib.compress(r,9)
    else:
        p=u(len(es))+b''.join(es);rec=records(rows,features(xs,es)) if rec is None else rec
        for y,rr in zip(rows,rec):
            opts=[b'\x00'+raw([y])]+[u(i+1)+rr[e] for i,e in enumerate(es)]
            p+=min(opts,key=lambda b:(len(b),b))
        if mode==b'H':p=zlib.compress(p,9)
    return h+p+digest
def decode(f,xs,inspect=False):
    r=Reader(f[:-32]);assert r.take(3)==b'LA1';mode=r.take(1);n,w=r.u(),r.u()
    if not 0<n<=256 or w!=len(xs) or not 0<w<=256 or r.take(32)!=input_hash(xs):raise ValueError('context')
    p=r.take(len(r.b)-r.p)
    if mode in (b'Z',b'H'):
        d=zlib.decompressobj();p=d.decompress(p,2_000_000)
        if not d.eof or d.unused_data or d.unconsumed_tail:raise ValueError('compressed payload')
    r=Reader(p);out=[];details=[];es=[]
    if mode in (b'M',b'H'):
        k=r.u()
        if k>128:raise ValueError('alphabet')
        for _ in range(k):
            e=r.take(1)
            if e[0]==8:e+=r.take(2)
            elif e[0]>=3:e+=r.take(1)
            valid=e in ATOMS or (e[0]==8 and e[1]<len(ATOMS) and e[2]<len(ATOMS) and e[1]!=e[2])
            if not valid or e in es:raise ValueError('expression')
            es.append(e)
        fs=features(xs,es)
    elif mode not in (b'R',b'Z'):raise ValueError('mode')
    for _ in range(n):
        tag=r.u() if mode in (b'M',b'H') else 0
        if tag==0:y=[r.s() for _ in range(w)];details.append({'primitive':'literal'})
        else:
            if tag>len(es):raise ValueError('index')
            e=es[tag-1];a,b=r.s(),r.s();kind=r.take(1);rr=[0]*w
            if kind==b'\x00':rr=[r.s() for _ in range(w)]
            elif kind==b'\x01':
                c=r.u();last=-1
                if c>w:raise ValueError('count')
                for _ in range(c):
                    i,v=r.u(),r.s()
                    if not last<i<w or not v:raise ValueError('patch')
                    rr[i]=v;last=i
            else:raise ValueError('residual mode')
            y=[a*v+b+d for v,d in zip(fs[e],rr)];details.append({'primitive':name(e),'scale':a,'offset':b,'residuals':[[i,v] for i,v in enumerate(rr) if v]})
        out.append(y)
    r.done()
    if hashlib.sha256(raw(out)).digest()!=f[-32:]:raise ValueError('digest')
    return (out,details) if inspect else out

def probe_bank(seed,n):
    r=random.Random(seed);return [[r.randint(-8,9) for _ in range(r.randint(1,5))] for _ in range(n)]
TRAIN_X=probe_bank(501,48);TEST_X=probe_bank(502,64)
# Synthetic reference families, deliberately similar to candidate grammar, not a blind corpus.
OPS={'sum':sum,'product':math.prod,'min':min,'max':max,'energy':lambda x:sum(v*v for v in x),'absolute_sum':lambda x:sum(abs(v) for v in x)}
def rows_for(coeffs,xs):
    names=[];rows=[]
    for k,f in OPS.items():
        for a,b in coeffs:names.append(f'{k}:{a}:{b}');rows.append([a*f(x)+b for x in xs])
    return names,rows
TRAIN_NAMES,TRAIN=rows_for([(1,0),(2,3),(-3,7),(4,-9)],TRAIN_X)
TEST_NAMES,TEST=rows_for([(3,11),(-2,-5),(7,4),(1,-13)],TEST_X)
OOD_OPS={'median_floor':lambda x:math.floor(statistics.median(x)),'span':lambda x:max(x)-min(x),'unique_count':lambda x:len(set(x)),'weighted_sum':lambda x:sum((i+1)*v for i,v in enumerate(x)),'sha_prefix':lambda x:int.from_bytes(hashlib.sha256(str(x).encode()).digest()[:3],'big'),'alternating_sum':lambda x:sum((-1)**i*v for i,v in enumerate(x))}
OOD_NAMES=[];OOD=[]
for k,f in OOD_OPS.items():
    for a,b in [(1,0),(3,11)]:OOD_NAMES.append(f'{k}:{a}:{b}');OOD.append([a*f(x)+b for x in TEST_X])

def learn(rows,xs):
    fs=features(xs,BASE+POOL);rec=records(rows,fs);es=list(BASE);trace=[]
    size=lambda es:len(frame(rows,xs,b'M',es,rec))
    while True:
        before=size(es);cost,e=min((size(es+[e]),e) for e in POOL if e not in es) if len(es)<1+len(POOL) else (before,b'')
        if cost>=before:break
        es.append(e);trace.append({'primitive':name(e),'definition_hex':e.hex(),'before':before,'after':cost,'saved':before-cost})
    return es,trace

def report(rows,xs,names,es):
    r=records(rows,features(xs,BASE+POOL));frames={'raw':frame(rows,xs,b'R'),'zlib':frame(rows,xs,b'Z'),'fixed':frame(rows,xs,b'M',BASE,r),'learned':frame(rows,xs,b'M',es,r),'hybrid':frame(rows,xs,b'H',es,r)}
    for f in frames.values():
        assert decode(f,xs)==rows
        try:decode(f[:-1]+bytes([f[-1]^1]),xs)
        except ValueError:pass
        else:raise AssertionError('tamper')
    _,d=decode(frames['learned'],xs,True)
    return {'bytes':{k:len(f) for k,f in frames.items()},'frames_hex':{k:f.hex() for k,f in frames.items()},'row_details':dict(zip(names,d))}

def predict(rows,xs,es,prefix=8):
    fs=features(xs,es);exact=0;cell=0;rows_detail=[]
    for y in rows:
        # choose only from prefix; score prefix exact wire cost + expression definition cost, deterministic tie break.
        cand=[]
        for e,x in fs.items():
            for a,b in fits(x[:prefix],y[:prefix]):
                rr=[v-a*w-b for v,w in zip(y[:prefix],x[:prefix])]
                cost=len(e)+len(s(a))+len(s(b))+len(residual(rr))
                cand.append((cost,e,a,b))
        _,e,a,b=min(cand);pred=[a*v+b for v in fs[e][prefix:]];matches=sum(a==b for a,b in zip(pred,y[prefix:]));cell+=matches;exact+=matches==len(pred);rows_detail.append({'primitive':name(e),'scale':a,'offset':b,'matches':matches})
    return {'exact_rows':exact,'rows':len(rows),'exact_cells':cell,'cells':len(rows)*(len(xs)-prefix),'details':rows_detail}

def main():
    es,trace=learn(TRAIN,TRAIN_X)
    result={'alphabet':[name(e) for e in es],'definition_bytes':sum(map(len,es)),'acquisition':trace,'training':report(TRAIN,TRAIN_X,TRAIN_NAMES,es),'heldout':report(TEST,TEST_X,TEST_NAMES,es),'out_of_family':report(OOD,TEST_X,OOD_NAMES,es),'prediction':{'fixed':predict(TEST,TEST_X,BASE),'learned':predict(TEST,TEST_X,es),'all_candidates':predict(TEST,TEST_X,BASE+POOL),'ood_learned':predict(OOD,TEST_X,es)},'probes':{'training':TRAIN_X,'heldout':TEST_X},'outputs':{'training':TRAIN,'heldout':TEST,'out_of_family':OOD}}
    # Frozen alphabet and per-row independent permutations. Preserve histograms; destroy input-output association.
    rng=random.Random(503);controls=[]
    for _ in range(100):
        rows=[rng.sample(y,len(y)) for y in TEST];r=records(rows,features(TEST_X,es));f=frame(rows,TEST_X,b'M',es,r);z=frame(rows,TEST_X,b'Z');assert decode(f,TEST_X)==rows;controls.append({'learned':len(f),'zlib':len(z)})
    result['shuffle']={k:{'mean':statistics.mean(x[k] for x in controls),'min':min(x[k] for x in controls),'max':max(x[k] for x in controls),'at_most_original':sum(x[k]<=result['heldout']['bytes'][k] for x in controls)} for k in ['learned','zlib']}
    result['shuffle_runs']=controls
    print(json.dumps(result,indent=2,sort_keys=True))
if __name__=='__main__':main()
