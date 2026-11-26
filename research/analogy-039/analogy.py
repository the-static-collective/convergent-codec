"""AN1: exact version spaces for reversible coordinate maps and global state flips.
No causal or semantic inference. A map is learned from paired ternary vectors.
"""
from itertools import permutations, product
from math import factorial
MAX_N=64
MAX_PAIRS=128

def need(ok,msg):
    if not ok: raise ValueError(msg)

def vector(x,n):
    need(len(x)==n and all(type(v) is int and 0<=v<=2 for v in x),'invalid vector')
    return tuple(x)

def flip(v,f): return 3-v if f and v else v

def apply(x,m,f=0):
    n=len(x); vector(x,n);need(sorted(m)==list(range(n)) and f in (0,1),'invalid map')
    return tuple(flip(x[i],f) for i in m)

def compose(a,b):
    """Apply a, then b. Maps are output-index -> input-index."""
    m,f=a; q,g=b;need(len(m)==len(q) and sorted(m)==sorted(q)==list(range(len(m))) and f in (0,1) and g in (0,1),'invalid composition')
    return tuple(m[i] for i in q),f^g

class Space:
    def __init__(self,n,pairs=()):
        need(type(n) is int and 1<=n<=MAX_N and len(pairs)<=MAX_PAIRS,'bounds')
        self.n=n; self.pairs=tuple((vector(x,n),vector(y,n)) for x,y in pairs);self.models=[]
        for f in (0,1):
            src={};dst={}
            for i in range(n):
                src.setdefault(tuple(flip(x[i],f) for x,y in self.pairs),[]).append(i)
                dst.setdefault(tuple(y[i] for x,y in self.pairs),[]).append(i)
            if src.keys()!=dst.keys() or any(len(src[k])!=len(dst[k]) for k in src):continue
            self.models.append((f,tuple((tuple(src[k]),tuple(dst[k])) for k in sorted(src))))
    def count(self):
        return sum(product_count(groups) for f,groups in self.models)
    def possibilities(self,x):
        x=vector(x,self.n);out=[set() for _ in x]
        for f,groups in self.models:
            for src,dst in groups:
                values={flip(x[i],f) for i in src}
                for j in dst:out[j].update(values)
        return tuple(frozenset(v) for v in out)
    def predict(self,x):
        p=self.possibilities(x)
        return tuple(next(iter(v)) for v in p) if all(len(v)==1 for v in p) else None
    def guess(self,x):
        if not self.models:return None
        f,groups=self.models[0];m=[None]*self.n
        for src,dst in groups:
            for i,j in zip(src,dst):m[j]=i
        return apply(x,m,f)
    def unique_map(self):
        if self.count()!=1:return None
        f,groups=self.models[0];m=[None]*self.n
        for src,dst in groups:m[dst[0]]=src[0]
        return tuple(m),f
    def refine(self,x,y):return Space(self.n,self.pairs+((x,y),))
    def query_score(self,x):
        """Expected log multiplicity reduction within each flip branch, uniform maps.
        Ignores information about flip identity; not a calibrated world probability."""
        from math import lgamma,log
        x=vector(x,self.n);total=self.count()
        if not total:return 0.
        value=0.
        for f,groups in self.models:
            weight=product_count(groups)/total
            for src,dst in groups:
                counts=[sum(x[i]==v for i in src) for v in range(3)]
                value+=weight*(lgamma(len(src)+1)-sum(lgamma(k+1) for k in counts))/log(2)
        return value

def product_count(groups):
    n=1
    for src,dst in groups:n*=factorial(len(src))
    return n

def axis_maps(rows,cols):
    need(1<=rows<=4 and 1<=cols<=4,'axis bounds')
    for a,b in product(permutations(range(rows)),permutations(range(cols))):
        yield tuple(a[r]*cols+b[c] for r in range(rows) for c in range(cols))
        if rows==cols:yield tuple(a[c]*cols+b[r] for r in range(rows) for c in range(cols))

class AxisSpace:
    def __init__(self,rows,cols,pairs):
        n=rows*cols; self.n=n; pairs=[(vector(x,n),vector(y,n)) for x,y in pairs]
        self.maps=[(m,f) for m in set(axis_maps(rows,cols)) for f in (0,1) if all(apply(x,m,f)==y for x,y in pairs)]
    def count(self):return len(self.maps)
    def predict(self,x):
        ys={apply(x,m,f) for m,f in self.maps};return next(iter(ys)) if len(ys)==1 else None

def chain_predict(a,b,x):
    """Exact marginal union over two independent version spaces, including ambiguous maps."""
    need(a.n==b.n,'chain size');p=a.possibilities(x);out=[set() for _ in p]
    if not a.count() or not b.count():return None
    for f,groups in b.models:
        for src,dst in groups:
            vs={flip(v,f) for i in src for v in p[i]}
            for j in dst:out[j].update(vs)
    return tuple(next(iter(v)) for v in out) if all(len(v)==1 for v in out) else None
