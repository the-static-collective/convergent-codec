"""IV1: mine translated cell compositions and pay for exact definitions/calls."""
import itertools,struct,functools,collections,zlib
import circulation as c
from accommodation import STATES,STATUS
MAX_RULES=12

def shift(x,t):
    return (((x//8+t//8)%4)*8+((x//2%4+t//2%4)%4)*2+(x%2^t%2))
def translate(shape,t):return tuple(sorted(shift(x,t) for x in shape))
def canonical(shape):return min(translate(shape,t) for t in range(32))
def valid(shape):return 3<=len(shape)<=16 and tuple(sorted(set(shape)))==shape and all(0<=x<32 for x in shape) and len({x//2 for x in shape})==len(shape)

def definitions(rules,recursive=True):
    c.need(len(rules)<=MAX_RULES and len(set(rules))==len(rules),'rule count')
    out=bytearray([len(rules)])
    for i,r in enumerate(rules):
        c.need(valid(r) and canonical(r)==r,'shape')
        choices=[bytes([len(r),*r])]
        if recursive:
            for j,q in enumerate(rules[:i]):
                for t in range(32):
                    a=set(translate(q,t))
                    if a<=set(r):
                        tail=sorted(set(r)-a);choices.append(bytes([128+len(tail),j,t,*tail]))
        out.extend(min(choices,key=lambda b:(len(b),b)))
    return bytes(out)

def read_defs(b):
    c.need(bool(b) and b[0]<=MAX_RULES,'definitions');i=1;rs=[]
    for _ in range(b[0]):
        c.need(i<len(b),'short rule');n=b[i];i+=1
        if n>=128:
            n-=128;c.need(i+2<=len(b) and b[i]<len(rs) and b[i+1]<32,'bad reference');r=translate(rs[b[i]],b[i+1]);i+=2
        else:r=()
        c.need(i+n<=len(b),'short shape');r=tuple(sorted(r+tuple(b[i:i+n])));i+=n
        c.need(valid(r) and canonical(r)==r and r not in rs,'invalid shape');rs.append(r)
    c.need(i==len(b),'definition trailing bytes');return rs

class Example:
    def __init__(self,f,truth):
        self.f=f;self.truth=truth;self.ops={};self.cells=[]
        for p,g,k in itertools.product(range(4),range(4),range(2)):
            x=p*8+g*2+k;a=dict.fromkeys(f.rows[p,g],STATUS[k]);self.ops[x]=a
            if a and all(truth.get(h)==v for h,v in a.items()):self.cells.append(x)
        self.cells=tuple(self.cells);self.target=sum(1<<x for x in self.cells)
        self.fixed=[]
        for x in self.cells:self.fixed.append((1<<x,bytes([x])))
        for i,a in enumerate(f.atoms):
            if a and all(truth.get(h)==v for h,v in a.items()):
                covered=tuple(x for x in self.cells if self.ops[x].keys()<=a.keys())
                if covered and set().union(*(self.ops[x].keys() for x in covered))==set(a):self.fixed.append((sum(1<<x for x in covered),bytes([32+i])))
        pred={h:v for x in self.cells for h,v in self.ops[x].items()};r=f.residual(truth,pred)
        self.residual=struct.pack('<H',len(r))+b''.join(struct.pack('<HB',i,v) for i,v in r)
        self.literal=bytes([0])+struct.pack('<H',len(truth))+b''.join(struct.pack('<HB',f.index[h],STATES.index(v)) for h,v in sorted(truth.items()))
        self.matches={}
    def match(self,r):
        if r not in self.matches:
            self.matches[r]=[(sum(1<<x for x in s),t) for t in range(32) for s in [translate(r,t)] if set(s)<=set(self.cells)]
        return self.matches[r]
    def encode(self,rules):
        opts=list(self.fixed)
        for i,r in enumerate(rules):opts.extend((m,bytes([128+i,t])) for m,t in self.match(r))
        by={x:[(m,b) for m,b in opts if m&(1<<x)] for x in self.cells}
        @functools.lru_cache(None)
        def best(mask):
            if not mask:return b''
            x=(mask&-mask).bit_length()-1
            return min((b+best(mask^m) for m,b in by[x] if m&mask==m),key=lambda b:(len(b),b))
        prog=best(self.target);wire=bytes([len(prog)])+prog+self.residual
        return min((wire,self.literal),key=lambda b:(len(b),b))

def decode(f,wire,rules):
    c.need(len(wire)>=3 and wire[0]+3<=len(wire),'frame');end=1+wire[0];i=1;out={}
    while i<end:
        x=wire[i];i+=1
        if x<32:ops=[x]
        elif x<128:
            c.need(x-32<len(f.atoms),'atom');out.update(f.atoms[x-32]);continue
        else:
            c.need(x-128<len(rules) and i<end and wire[i]<32,'macro');ops=translate(rules[x-128],wire[i]);i+=1
        for a in ops:out.update(dict.fromkeys(f.rows[a//8,a//2%4],STATUS[a%2]))
    count=struct.unpack_from('<H',wire,end)[0];c.need(len(wire)==end+2+3*count,'residual length');last=-1
    for j,v in struct.iter_unpack('<HB',wire[end+2:]):
        c.need(last<j<len(f.keys) and v<len(STATES),'residual');last=j;h=f.keys[j];x=STATES[v]
        if x==f.base[h]:out.pop(h,None)
        else:out[h]=x
    return out

def mine(examples):
    support=collections.Counter()
    for e in examples:
        seen=set()
        for n in range(3,min(6,len(e.cells))+1):
            seen.update(canonical(s) for s in itertools.combinations(e.cells,n))
        if len(e.cells)>6:seen.add(canonical(e.cells))
        support.update(seen)
    return sorted((r for r,n in support.items() if n>=3),key=lambda r:(-support[r]*(len(r)-2),r))[:24]

def stream(examples,rules,recursive=True):
    d=definitions(rules,recursive);out=bytearray(struct.pack('<H',len(d))+d)
    for e in examples:
        b=e.encode(rules);out.extend(struct.pack('<H',len(b))+b)
    return bytes(out)
def train(examples,entropy=False):
    pool=mine(examples);rules=[];history=[]
    def cost(rs):
        b=stream(examples,rs);return len(zlib.compress(b,9)) if entropy else len(b)
    current=cost(rules)
    while pool and len(rules)<MAX_RULES:
        n,r=min((cost(rules+[r]),r) for r in pool)
        if n>=current:break
        history.append((r,current,n));rules.append(r);pool.remove(r);current=n
    return rules,history

def verify(examples,wire):
    n=struct.unpack_from('<H',wire)[0];rs=read_defs(wire[2:2+n]);i=2+n
    for e in examples:
        c.need(i+2<=len(wire),'frame length');n=struct.unpack_from('<H',wire,i)[0];i+=2;c.need(i+n<=len(wire),'short record');c.need(decode(e.f,wire[i:i+n],rs)==e.truth,'roundtrip');i+=n
    c.need(i==len(wire),'trailing bytes');return rs

def grid_stream(examples):
    """Strong fixed 2-bit per cell representation, same exact residuals and frame lengths."""
    out=bytearray()
    for e in examples:
        v=sum((1+x%2)<<(2*(x//2)) for x in e.cells)
        b=struct.pack('<I',v)+e.residual;out.extend(struct.pack('<H',len(b))+b)
    return bytes(out)

def verify_grid(examples,wire):
    i=0
    for e in examples:
        c.need(i+2<=len(wire),'grid frame');n=struct.unpack_from('<H',wire,i)[0];i+=2;c.need(n>=6 and i+n<=len(wire),'grid length')
        v=struct.unpack_from('<I',wire,i)[0];ops=[]
        for j in range(16):
            a=(v>>(2*j))&3;c.need(a!=3,'invalid grid cell')
            if a:ops.append(j*2+a-1)
        b=bytes([len(ops),*ops])+wire[i+4:i+n];c.need(decode(e.f,b,[])==e.truth,'grid roundtrip');i+=n
    c.need(i==len(wire),'grid trailing bytes')
