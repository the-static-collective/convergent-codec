"""CW1 local multi-peer CC1 recovery. No network or remote execution."""
import argparse, json, os, struct, tempfile, zlib
from pathlib import Path
import circulation as c

MAX_PEERS=32

def bitmap(refs, known):
    known=set(known); b=bytearray((len(refs)+7)//8)
    for i,h in enumerate(refs):
        if h in known:b[i//8]|=1<<(i%8)
    return bytes(b)

def unbitmap(refs,b):
    c.need(len(b)==(len(refs)+7)//8,'bitmap length')
    c.need(not refs or len(refs)%8==0 or b[-1]>>(len(refs)%8)==0,'bitmap padding')
    return {h for i,h in enumerate(refs) if b[i//8]&(1<<(i%8))}

def read_object(store,h):
    try:
        p=Path(store)/h
        if not p.is_file() or p.is_symlink():return None,0
        wire=c.read_limited(p,c.MAX_CHUNK+1)
        try:
            b=c.object_decode(wire)
            if c.digest(b)==h:return b,len(wire)
        except (c.Error,UnicodeError):pass
        return None,len(wire)
    except (OSError,c.Error):return None,0

def save_object(store,h,b):
    c.need(c.valid_hash(h) and c.digest(b)==h,'object mismatch')
    store=Path(store); c.need(not store.is_symlink(),'symlink store');store.mkdir(parents=True,exist_ok=True)
    p=store/h;c.need(not p.is_symlink(),'symlink object')
    fd,tmp=tempfile.mkstemp(dir=store)
    try:
        with os.fdopen(fd,'wb') as f:f.write(c.object_encode(b))
        os.replace(tmp,p)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def recover(m,expected,stores,local,destination,mode='bitmap',advertised=None,offline=(),shared_manifest=True):
    """advertised/offline simulate stale advertisements and unavailable peers.
    Wire accounting models an explicit protocol; filesystem reads are real."""
    refs=sorted(c.validate(m)); pin=c.digest(c.canon(m));c.need(pin==expected,'manifest pin mismatch')
    c.need(0<len(stores)<=MAX_PEERS and mode in ('bitmap','exact','blind'),'peer or mode limit')
    paths=[Path(p).resolve() for p in [*stores,local,destination]]
    c.need(len(set(paths))==len(paths),'distinct stores and destination required')
    c.need(not Path(destination).exists() and not Path(destination).is_symlink(),'destination exists')
    for p in stores:c.need(not Path(p).is_symlink(),'symlink peer')
    c.need(not Path(local).is_symlink(),'symlink local')
    known=set(c.inventory(local)); missing=set(refs)-known
    stats=dict(manifest_bytes=len(c.make_bundle(m,{},refs)),inventory_bytes=0,request_bytes=0,response_bytes=0,requests=0,failed_requests=0,received=0,reused=len(set(refs)&known),peer_objects=[0]*len(stores))
    ads=[]; unavailable=set(offline)
    for i,p in enumerate(stores):
        if i in unavailable:ads.append(set());continue
        if mode=='blind':ads.append(set());continue
        a=set(advertised[i]) if advertised is not None else set(c.inventory(p))
        if mode=='bitmap':
            msg=bitmap(refs,a);ads.append(unbitmap(refs,msg));stats['inventory_bytes']+=32+4+len(msg)
            if not shared_manifest:stats['inventory_bytes']+=stats['manifest_bytes']
        else:
            msg=c.inventory_wire(a);ads.append(set(c.parse_inventory(msg)));stats['inventory_bytes']+=len(msg)
    found={}; unresolved=[]
    # Rarest first, then distribute across peers by number of successful objects.
    for h in sorted(missing,key=lambda h:(sum(h in a for a in ads),h)):
        order=sorted(range(len(stores)),key=lambda i:(i in unavailable, h not in ads[i],stats['peer_objects'][i],i)) if mode!='blind' else range(len(stores))
        for i in order:
            if i in unavailable:continue
            stats['requests']+=1;stats['request_bytes']+=32
            b,n=read_object(stores[i],h);stats['response_bytes']+=1+(4+n if n else 0)
            if b is None:stats['failed_requests']+=1;continue
            found[h]=b;stats['received']+=1;stats['peer_objects'][i]+=1;break
        else:unresolved.append(h)
    stats['missing']=unresolved;stats['wire_bytes']=sum(stats[k] for k in ('manifest_bytes','inventory_bytes','request_bytes','response_bytes'))
    # Cache verified discoveries even if complete restoration is impossible.
    for h,b in found.items():save_object(local,h,b)
    if not unresolved:
        c.receive(c.make_bundle(m,{},refs),local,destination);stats['restored']=True
    else:stats['restored']=False
    return stats

def replicate(refs,stores,budget,policy='scarcity',target=3,seed=24):
    """Copy at most budget encoded object bytes (payload only), no deletions."""
    import random
    c.need(0<len(stores)<=MAX_PEERS and len(set(Path(p).resolve() for p in stores))==len(stores),'invalid peers')
    c.need(budget>=0 and 1<=target<=len(stores) and policy in ('scarcity','random'),'invalid replication settings')
    for p in stores:c.need(not Path(p).is_symlink(),'symlink peer')
    refs=sorted(set(refs));c.need(len(refs)<=c.MAX_OBJECTS and all(c.valid_hash(h) for h in refs),'invalid references')
    inventories=[set(c.inventory(p)) for p in stores];rng=random.Random(seed);spent=0;copies=0
    while True:
        candidates=[(sum(h in a for a in inventories),h) for h in refs if 0<sum(h in a for a in inventories)<target]
        if policy=='scarcity':candidates.sort()
        else:rng.shuffle(candidates)
        for count,h in candidates:
            b=next((b for i,p in enumerate(stores) if h in inventories[i] for b,_ in [read_object(p,h)] if b is not None),None)
            if b is None:continue
            cost=len(c.object_encode(b))
            if spent+cost>budget:continue
            i=min((i for i,a in enumerate(inventories) if h not in a),key=lambda i:(len(inventories[i]),i))
            save_object(stores[i],h,b);inventories[i].add(h);spent+=cost;copies+=1;break
        else:break
    return {'payload_bytes':spent,'copies':copies,'counts':{h:sum(h in a for a in inventories) for h in refs}}

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='cmd',required=True)
    q=sub.add_parser('manifest');q.add_argument('source');q.add_argument('output');q.add_argument('store')
    q=sub.add_parser('recover');q.add_argument('manifest');q.add_argument('pin');q.add_argument('local');q.add_argument('destination');q.add_argument('peers',nargs='+');q.add_argument('--mode',choices=['bitmap','exact','blind'],default='bitmap')
    q=sub.add_parser('replicate');q.add_argument('manifest');q.add_argument('pin');q.add_argument('budget',type=int);q.add_argument('peers',nargs='+');q.add_argument('--target',type=int,default=3)
    a=p.parse_args()
    try:
        if a.cmd=='manifest':
            m,o=c.snapshot(a.source)
            with open(a.output,'xb') as f:f.write(c.canon(m))
            for h,b in o.items():save_object(a.store,h,b)
            result={'pin':c.digest(c.canon(m)),'objects':len(o)}
        else:
            m=json.loads(c.read_limited(a.manifest,c.MAX_MANIFEST));c.need(c.digest(c.canon(m))==a.pin,'manifest pin mismatch')
            if a.cmd=='recover':result=recover(m,a.pin,a.peers,a.local,a.destination,a.mode)
            else:result=replicate(c.validate(m),a.peers,a.budget,target=a.target)
        print(json.dumps(result,indent=2))
        if result.get('restored') is False:p.exit(3,'incomplete recovery; verified objects cached\n')
    except (OSError,ValueError,UnicodeError,RecursionError) as e:p.exit(2,f'CW1: {e}\n')
if __name__=='__main__':main()
