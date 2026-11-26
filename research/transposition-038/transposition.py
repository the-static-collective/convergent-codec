"""TP1: paid structural transfer of learned IV1 calls across peer/group permutations."""
import itertools,struct,functools,zlib,hashlib
import circulation as c
import invention as v
import metamorphosis as m
from accommodation import STATUS
PERMS=tuple(itertools.permutations(range(4)))
MAPS=tuple((a,b,s) for a in PERMS for b in PERMS for s in (0,1))
MAX_MAP=len(MAPS)

def transform(x,k):
    a,b,s=MAPS[k];p,g=x//8,x//2%4
    if s:p,g=g,p
    return a[p]*8+b[g]*2+x%2

def mapped(r,t,k):return tuple(sorted(transform(x,k) for x in v.translate(r,t)))

def orbit(r,k):return tuple((sum(1<<x for x in mapped(r,t,k)),t) for t in range(32))

def mapped_records(ex,rules,k):
    opts=[(mask,bytes([128+i,t])) for i,r in enumerate(rules) for mask,t in orbit(r,k)]
    out=bytearray()
    for e in ex:
        available=e.fixed+[(a,b) for a,b in opts if a&e.target==a]
        by={x:[(a,b) for a,b in available if a&(1<<x)] for x in e.cells}
        @functools.lru_cache(None)
        def best(mask):
            if not mask:return b''
            x=(mask&-mask).bit_length()-1
            return min((b+best(mask^a) for a,b in by[x] if a&mask==a),key=lambda b:(len(b),b))
        prog=best(e.target);wire=min((bytes([len(prog)])+prog+e.residual,e.literal),key=lambda b:(len(b),b))
        out.extend(struct.pack('<H',len(wire))+wire)
    return bytes(out)

@functools.lru_cache(maxsize=2)
def orbit_index(rules):
    return tuple(tuple((mask,len(r)-2) for r in rules for mask,_ in orbit(r,k)) for k in range(MAX_MAP))

def shortlist(ex,rules,limit=6):
    # Cheap support proxy, not exhaustive compressed-byte optimization.
    from collections import Counter
    counts=Counter(e.target for e in ex);rank=[]
    for k,os in enumerate(orbit_index(tuple(rules))):
        value=sum(n*max((gain for mask,gain in os if mask&target==mask),default=0) for target,n in counts.items())
        if value:rank.append((-value,k))
    return [k for _,k in sorted(rank)[:limit]]

def decode_mapped(f,b,rules,k):
    c.need(len(b)>=3 and b[0]+3<=len(b),'record');end=1+b[0];i=1;ops=[]
    while i<end:
        x=b[i];i+=1
        if x<128:ops.append(x)
        else:
            c.need(x-128<len(rules) and i<end and b[i]<32,'mapped call');ops.extend(mapped(rules[x-128],b[i],k));i+=1
    c.need(len(ops)<=255,'expansion bound');return v.decode(f,bytes([len(ops),*ops])+b[end:],[])

def encode(blocks,source,policy,learned=None):
    c.need(policy in ('grid','generic','fresh','direct','transfer','hybrid') and 0<len(blocks)<=4096,'policy')
    rs=source if policy in ('direct','transfer','hybrid') else []
    defs=v.definitions(rs);out=bytearray(b'TP1\0'+struct.pack('<HH',len(blocks),len(defs))+defs);log=[]
    for i,ex in enumerate(blocks):
        c.need(0<len(ex)<=64,'block size');opts=[]
        if policy!='grid':opts.append((m.packet(0,m.records(ex,[])),'generic'))
        if policy!='generic':opts.append((m.packet(1,v.grid_stream(ex)),'grid'))
        if policy in ('fresh','hybrid'):
            r=learned[i] if learned is not None else v.train(ex,True)[0]
            if r:opts.append((m.new_packet(ex,r),'fresh'))
        if rs:
            opts.append((m.packet(3,m.records(ex,rs)),'direct'))
            if policy in ('transfer','hybrid'):
                for k in shortlist(ex,rs):opts.append((m.packet(4,struct.pack('<H',k)+mapped_records(ex,rs,k)),'transfer'))
        b,kind=min(opts,key=lambda x:(len(x[0]),x[0]));out.extend(struct.pack('<HI',len(ex),len(b)));out.extend(b);log.append((kind,len(b)+6))
    return bytes(out)+hashlib.sha256(out).digest(),log

def decode(fields,wire):
    c.need(41<=len(wire)<=c.MAX_WIRE and wire[:4]==b'TP1\0' and hashlib.sha256(wire[:-32]).digest()==wire[-32:],'stream')
    n,k=struct.unpack_from('<HH',wire,4);end=len(wire)-32;c.need(0<n<=4096 and n==len(fields) and 8+k<=end,'header');source=v.read_defs(wire[8:8+k]);i=8+k;result=[]
    for fs in fields:
        c.need(i+6<=end,'block header');count,size=struct.unpack_from('<HI',wire,i);i+=6;c.need(0<count<=64 and count==len(fs) and 1<size<=m.MAX_RAW and i+size<=end,'block bounds')
        mode=wire[i];raw=c.inflate(wire[i+1:i+size],m.MAX_RAW);i+=size;j=0;rs=[];mapping=None
        if mode==2:
            c.need(len(raw)>=2,'definition header');k=struct.unpack_from('<H',raw)[0];c.need(0<k<=len(raw)-2,'definition bounds');rs=v.read_defs(raw[2:2+k]);j=2+k
        elif mode==3:rs=source
        elif mode==4:
            c.need(len(raw)>=2 and bool(source),'mapping header');mapping=struct.unpack_from('<H',raw)[0];c.need(mapping<MAX_MAP,'mapping bounds');rs=source;j=2
        else:c.need(mode in (0,1),'mode')
        block=[]
        for f in fs:
            c.need(j+2<=len(raw),'record header');k=struct.unpack_from('<H',raw,j)[0];j+=2;c.need(j+k<=len(raw),'record size');b=raw[j:j+k];j+=k
            if mode==1:
                c.need(len(b)>=6,'grid');value=struct.unpack_from('<I',b)[0];ops=[]
                for cell in range(16):
                    a=value>>(2*cell)&3;c.need(a!=3,'grid cell')
                    if a:ops.append(cell*2+a-1)
                b=bytes([len(ops),*ops])+b[4:]
            block.append(decode_mapped(f,b,rs,mapping) if mapping is not None else v.decode(f,b,rs))
        c.need(j==len(raw),'trailing record bytes');result.append(block)
    c.need(i==end,'trailing stream bytes');return result
