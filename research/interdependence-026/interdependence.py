"""ID1 bounded finite-field erasure recovery over pinned CC1 object manifests."""
import argparse,json
from pathlib import Path
import circulation as c
import commonwealth as w
MAX_VARS=128
MAX_ROWS=128
MAX_MEMBERS=8

def mul(a,b):
    v=0
    while b:
        if b&1:v^=a
        b>>=1;a<<=1
        if a&256:a^=0x11d
    return v
TABLE=[bytes(mul(a,b) for b in range(256)) for a in range(256)]
INV=[0]+[TABLE[a].index(1) for a in range(1,256)]

def scale(b,a):return b.translate(TABLE[a])
def add(a,b):
    n=max(len(a),len(b));return (int.from_bytes(a,'little')^int.from_bytes(b,'little')).to_bytes(n,'little')

def validate(r):
    c.need(isinstance(r,dict) and set(r)=={'members','parity'} and c.valid_hash(r['parity']),'equation schema')
    m=r['members'];c.need(isinstance(m,list) and 2<=len(m)<=MAX_MEMBERS,'member count')
    c.need(all(isinstance(t,list) and len(t)==3 and c.valid_hash(t[0]) and type(t[1]) is int and 0<t[1]<=c.MAX_CHUNK and type(t[2]) is int and 0<t[2]<=255 for t in m),'member schema')
    hs=[t[0] for t in m];c.need(hs==sorted(set(hs)),'member order');return hs

def equation(objects,coeff):
    c.need(2<=len(coeff)<=MAX_MEMBERS,'member count');p=b'';ms=[]
    for h,a in sorted(coeff.items()):
        b=objects[h];c.need(c.digest(b)==h and 0<len(b)<=c.MAX_CHUNK and type(a) is int and 0<a<=255,'invalid member')
        ms.append([h,len(b),a]);p=add(p,scale(b,a))
    r={'members':ms,'parity':c.digest(p)};validate(r);return r,p

def reduce_rows(rows,n):
    """RREF with optional RHS bytes. Returns pivot rows and detects contradictions."""
    c.need(n<=MAX_VARS and len(rows)<=MAX_ROWS,'solver bounds')
    basis={}
    for a,b in rows:
        a=list(a);c.need(len(a)==n and len(b)<=c.MAX_CHUNK,'row bounds')
        for j,(p,q) in sorted(basis.items()):
            k=a[j]
            if k:a=[x^TABLE[k][y] for x,y in zip(a,p)];b=add(b,scale(q,k))
        j=next((j for j,v in enumerate(a) if v),None)
        if j is None:
            c.need(not any(b),'inconsistent equations');continue
        k=INV[a[j]];a=[TABLE[k][v] for v in a];b=scale(b,k)
        for i,(p,q) in list(basis.items()):
            k=p[j]
            if k:basis[i]=([x^TABLE[k][y] for x,y in zip(p,a)],add(q,scale(b,k)))
        basis[j]=(a,b)
    return basis

def solve(refs,records,known,parity,method='linear'):
    c.need(len(refs)<=MAX_VARS and len(records)<=MAX_ROWS and method in ('linear','peeling'),'solver bounds')
    refs=set(refs);sizes={};known=dict(known)
    for h,b in known.items():c.need(h in refs and c.digest(b)==h,'invalid known object')
    for r in records:
        c.need(set(validate(r))<=refs,'unknown member')
        for h,n,a in r['members']:
            c.need(sizes.setdefault(h,n)==n and (h not in known or len(known[h])==n),'inconsistent size')
    valid=[]
    for r in records:
        p=parity.get(r['parity'])
        if p is not None and len(p)==max(t[1] for t in r['members']) and c.digest(p)==r['parity']:valid.append((r,p))
    def admit(h,b):
        n=sizes[h];c.need(len(b)>=n and not any(b[n:]) and c.digest(b[:n])==h,'reconstruction digest mismatch');known[h]=b[:n]
    if method=='peeling':
        while True:
            old=len(known)
            for r,p in valid:
                missing=[(h,a) for h,n,a in r['members'] if h not in known]
                if len(missing)!=1:continue
                for h,n,a in r['members']:
                    if h in known:p=add(p,scale(known[h],a))
                h,a=missing[0];admit(h,scale(p,INV[a]))
            if len(known)==old:break
        return known
    unknown=sorted(refs-known.keys());idx={h:i for i,h in enumerate(unknown)};rows=[]
    for r,p in valid:
        a=[0]*len(unknown)
        for h,n,k in r['members']:
            if h in known:p=add(p,scale(known[h],k))
            else:a[idx[h]]=k
        rows.append((a,p))
    for j,(a,b) in reduce_rows(rows,len(unknown)).items():
        if sum(bool(x) for x in a)==1:admit(unknown[j],b)
    return known

def restore(m,pin,records,record_pin,peers,local,dest,method='linear'):
    refs=c.validate(m);c.need(len(refs)<=MAX_VARS and isinstance(records,list) and len(records)<=MAX_ROWS,'solver bounds')
    c.need(c.digest(c.canon(m))==pin and c.digest(c.canon(records))==record_pin,'pin mismatch')
    c.need(0<len(peers)<=32 and len({Path(p).resolve() for p in [*peers,local,dest]})==len(peers)+2,'distinct paths required')
    c.need(not Path(dest).exists() and not Path(dest).is_symlink() and all(not Path(p).is_symlink() for p in [*peers,local]),'unsafe paths')
    for r in records:c.need(set(validate(r))<=refs,'unknown member')
    reads=0;read_bytes=0
    def read(h):
        nonlocal reads,read_bytes
        for p in [local,*peers]:
            b,n=w.read_object(p,h);reads+=1;read_bytes+=n
            if b is not None:return b
    known={h:b for h in sorted(refs) if (b:=read(h)) is not None}
    parity={h:b for h in sorted({r['parity'] for r in records}) if (b:=read(h)) is not None}
    out=solve(refs,records,known,parity,method)
    for h,b in out.items():w.save_object(local,h,b)
    missing=sorted(refs-out.keys())
    if not missing:c.receive(c.make_bundle(m,{},refs),local,dest)
    return {'restored':not missing,'direct':len(known),'regenerated':len(out)-len(known),'missing':missing,'reads':reads,'read_bytes':read_bytes}

def main():
    p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='cmd',required=True)
    q=s.add_parser('protect');q.add_argument('source_store');q.add_argument('parity_store');q.add_argument('records');q.add_argument('members',nargs='+',help='hash:coefficient, decimal coefficient 1..255')
    q=s.add_parser('recover');q.add_argument('manifest');q.add_argument('pin');q.add_argument('records');q.add_argument('record_pin');q.add_argument('local');q.add_argument('destination');q.add_argument('peers',nargs='+');q.add_argument('--method',choices=['linear','peeling'],default='linear')
    a=p.parse_args()
    try:
        if a.cmd=='protect':
            coeff={h:int(k) for h,k in (x.split(':') for x in a.members)};c.need(len(coeff)==len(a.members) and all(c.valid_hash(h) for h in coeff),'invalid members')
            obj={h:w.read_object(a.source_store,h)[0] for h in coeff};c.need(all(b is not None for b in obj.values()),'missing object');r,b=equation(obj,coeff);w.save_object(a.parity_store,r['parity'],b)
            raw=c.canon([r]);Path(a.records).open('xb').write(raw);result={'record_pin':c.digest(raw),'parity':r['parity']}
        else:
            m=json.loads(c.read_limited(a.manifest,c.MAX_MANIFEST));rs=json.loads(c.read_limited(a.records,c.MAX_MANIFEST));result=restore(m,a.pin,rs,a.record_pin,a.peers,a.local,a.destination,a.method)
        print(json.dumps(result,indent=2))
        if result.get('restored') is False:p.exit(3,'incomplete recovery; verified material retained\n')
    except (OSError,ValueError,RecursionError) as e:p.exit(2,f'ID1: {e}\n')
if __name__=='__main__':main()
