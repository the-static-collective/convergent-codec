"""FC1: pinned XOR parity records over CC1 objects; local research only."""
import argparse,json,os,itertools,random
from pathlib import Path
import circulation as c
import commonwealth as w
MAX_GROUP=8

def xor(parts):
    out=bytearray(max(map(len,parts),default=0))
    for b in parts:
        for i,v in enumerate(b):out[i]^=v
    return bytes(out)

def make_record(objects, members):
    members=sorted(members);c.need(2<=len(members)<=MAX_GROUP and len(set(members))==len(members),'group bounds')
    bs=[objects[h] for h in members];c.need(all(0<len(b)<=c.MAX_CHUNK and c.digest(b)==h for h,b in zip(members,bs)),'bad member')
    p=xor(bs);return {'members':[[h,len(b)] for h,b in zip(members,bs)],'parity':c.digest(p)},p

def validate_record(r):
    c.need(isinstance(r,dict) and set(r)=={'members','parity'} and c.valid_hash(r['parity']),'record schema')
    ms=r['members'];c.need(isinstance(ms,list) and 2<=len(ms)<=MAX_GROUP,'group bounds')
    c.need(all(isinstance(x,list) and len(x)==2 and c.valid_hash(x[0]) and type(x[1]) is int and 0<x[1]<=c.MAX_CHUNK for x in ms),'member schema')
    hs=[x[0] for x in ms];c.need(hs==sorted(set(hs)),'member order');return hs

def recover_record(r,known,p):
    hs=validate_record(r);sizes=dict(r['members']);c.need(len(p)==max(sizes.values()) and c.digest(p)==r['parity'],'bad parity')
    missing=[h for h in hs if h not in known]
    if len(missing)!=1:return None
    for h in hs:
        if h in known:c.need(len(known[h])==sizes[h] and c.digest(known[h])==h,'bad input object')
    h=missing[0];b=xor([p]+[known[k] for k in hs if k!=h])[:sizes[h]];c.need(c.digest(b)==h,'reconstruction digest mismatch');return h,b

def recover(m,pin,records,record_pin,peers,local,dest,offline=()):
    refs=c.validate(m);c.need(c.digest(c.canon(m))==pin and c.digest(c.canon(records))==record_pin,'pin mismatch')
    c.need(isinstance(records,list) and len(records)<=c.MAX_OBJECTS,'record count')
    c.need(all(set(validate_record(r))<=refs for r in records),'unknown member')
    c.need(0<len(peers)<=32 and len({Path(p).resolve() for p in [*peers,local,dest]})==len(peers)+2,'distinct stores')
    c.need(not Path(dest).exists() and not Path(dest).is_symlink(),'destination exists')
    c.need(all(not Path(p).is_symlink() for p in [*peers,local]),'symlink store')
    sources=[local]+[p for i,p in enumerate(peers) if i not in offline];known={};reads=0;read_bytes=0
    def read(h):
        nonlocal reads,read_bytes
        for p in sources:
            b,n=w.read_object(p,h);reads+=1;read_bytes+=n
            if b is not None:return b
    for h in sorted(refs):
        b=read(h)
        if b is not None:known[h]=b
    direct=len(known);used=0;parities={}
    while True:
        progress=False
        for r in records:
            hs=[h for h,n in r['members']]
            if sum(h not in known for h in hs)!=1:continue
            ph=r['parity']
            if ph not in parities:parities[ph]=read(ph)
            if parities[ph] is None:continue
            try:result=recover_record(r,known,parities[ph])
            except c.Error:continue
            if result:
                h,b=result;known[h]=b;progress=True;used+=1
        if not progress:break
    for h,b in known.items():w.save_object(local,h,b)
    missing=sorted(refs-known.keys())
    if not missing:c.receive(c.make_bundle(m,{},refs),local,dest)
    return {'restored':not missing,'direct':direct,'regenerated':used,'missing':missing,'reads':reads,'read_bytes':read_bytes}

def main():
    p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='cmd',required=True)
    q=s.add_parser('protect');q.add_argument('store');q.add_argument('parity_store');q.add_argument('records');q.add_argument('members',nargs='+')
    q=s.add_parser('recover');q.add_argument('manifest');q.add_argument('pin');q.add_argument('records');q.add_argument('record_pin');q.add_argument('local');q.add_argument('destination');q.add_argument('peers',nargs='+')
    a=p.parse_args()
    try:
        if a.cmd=='protect':
            c.need(2<=len(a.members)<=MAX_GROUP and all(c.valid_hash(h) for h in a.members),'invalid members')
            obj={h:w.read_object(a.store,h)[0] for h in a.members};c.need(all(b is not None for b in obj.values()),'missing object');r,b=make_record(obj,a.members);w.save_object(a.parity_store,r['parity'],b)
            raw=c.canon([r]);
            with open(a.records,'xb') as f:f.write(raw)
            result={'record_pin':c.digest(raw),'metadata_bytes':len(raw),'parity_bytes':len(c.object_encode(b))}
        else:
            m=json.loads(c.read_limited(a.manifest,c.MAX_MANIFEST));rs=json.loads(c.read_limited(a.records,c.MAX_MANIFEST));result=recover(m,a.pin,rs,a.record_pin,a.peers,a.local,a.destination)
        print(json.dumps(result,indent=2))
        if result.get('restored') is False:p.exit(3,'incomplete recovery; verified objects retained\n')
    except (ValueError,OSError,RecursionError) as e:p.exit(2,f'FC1: {e}\n')
if __name__=='__main__':main()
