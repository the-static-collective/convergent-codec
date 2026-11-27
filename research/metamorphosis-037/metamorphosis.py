"""MT1: bounded dictionary resurrection over independently framed IV1 blocks."""
import struct,zlib,hashlib
import circulation as c
import invention as v
MAGIC=b'MT1\0'; MAX_BLOCK=64; MAX_BLOCKS=4096; MAX_RAW=1<<20
POLICIES=('generic','grid','fixed','reset','hot','archive')

def records(ex,rules):
    out=bytearray()
    for e in ex:
        b=e.encode(rules);out.extend(struct.pack('<H',len(b))+b)
    return bytes(out)

def packet(mode,raw):return bytes([mode])+zlib.compress(raw,9)

def new_packet(ex,rules):
    d=v.definitions(rules);return packet(2,struct.pack('<H',len(d))+d+records(ex,rules))

def touch(cache,rules,cap):
    if rules in cache:cache.remove(rules)
    cache.insert(0,rules);del cache[cap:]

def encode(blocks,policy,cap=4,learned=None):
    c.need(policy in POLICIES and 1<=cap<=8 and 0<len(blocks)<=MAX_BLOCKS,'policy or bounds')
    cap=1 if policy!='archive' else cap
    out=bytearray(MAGIC+bytes([cap])+struct.pack('<H',len(blocks)));cache=[];log=[]
    if learned is not None:c.need(len(learned)==len(blocks),'training count')
    for i,ex in enumerate(blocks):
        c.need(0<len(ex)<=MAX_BLOCK,'block count')
        options=[]
        if policy!='grid':options.append((packet(0,records(ex,[])),None,'generic'))
        if policy!='generic':options.append((packet(1,v.grid_stream(ex)),None,'grid'))
        if policy in ('fixed','hot','archive'):
            for j,r in enumerate(cache):options.append((packet(3,bytes([j])+records(ex,r)),r,'hot' if j==0 else 'dormant'))
        if policy in ('reset','hot','archive') or (policy=='fixed' and i==0):
            r=tuple(learned[i] if learned is not None else v.train(ex,True)[0])
            if r and (policy=='reset' or r not in cache):options.append((new_packet(ex,r),r,'install'))
        b,r,kind=min(options,key=lambda x:(len(x[0]),x[0]))
        if r is not None:touch(cache,r,cap)
        out.extend(struct.pack('<HI',len(ex),len(b)));out.extend(b)
        log.append({'kind':kind,'bytes':6+len(b),'cache_bytes':sum(len(v.definitions(q))+2 for q in cache),'cache_entries':len(cache)})
    return bytes(out)+hashlib.sha256(out).digest(),log

def decode(fields,wire):
    c.need(39<=len(wire)<=c.MAX_WIRE and wire[:4]==MAGIC and hashlib.sha256(wire[:-32]).digest()==wire[-32:],'stream digest or header')
    cap=wire[4];n=struct.unpack_from('<H',wire,5)[0];c.need(1<=cap<=8 and 0<n<=MAX_BLOCKS and n==len(fields),'stream bounds')
    end=len(wire)-32;i=7;cache=[];result=[]
    for fs in fields:
        c.need(i+6<=end,'block header');count,size=struct.unpack_from('<HI',wire,i);i+=6
        c.need(0<count<=MAX_BLOCK and count==len(fs) and 1<size<=MAX_RAW and i+size<=end,'block bounds')
        mode=wire[i];raw=c.inflate(wire[i+1:i+size],MAX_RAW);i+=size;j=0;rs=[]
        if mode==2:
            c.need(len(raw)>=2,'dictionary header');k=struct.unpack_from('<H',raw)[0];c.need(0<k<=len(raw)-2,'dictionary bounds');rs=tuple(v.read_defs(raw[2:2+k]));c.need(bool(rs),'empty dictionary');j=2+k;touch(cache,rs,cap)
        elif mode==3:
            c.need(bool(raw) and raw[0]<len(cache),'missing dictionary');rs=cache[raw[0]];j=1;touch(cache,rs,cap)
        else:c.need(mode in (0,1),'block mode')
        block=[]
        for f in fs:
            c.need(j+2<=len(raw),'record header');k=struct.unpack_from('<H',raw,j)[0];j+=2;c.need(j+k<=len(raw),'record size');b=raw[j:j+k];j+=k
            if mode==1:
                c.need(len(b)>=6,'grid length');value=struct.unpack_from('<I',b)[0];ops=[]
                for cell in range(16):
                    a=(value>>(2*cell))&3;c.need(a!=3,'grid cell')
                    if a:ops.append(cell*2+a-1)
                b=bytes([len(ops),*ops])+b[4:]
            block.append(v.decode(f,b,rs))
        c.need(j==len(raw),'block trailing bytes');result.append(block)
    c.need(i==end,'stream trailing bytes');return result
