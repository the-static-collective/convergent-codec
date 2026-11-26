"""CC1 research snapshots: content-addressed, bounded, non-destructive transfer."""
import argparse, hashlib, json, os, re, shutil, struct, tempfile, zlib
from pathlib import Path
import ec1

MAGIC=b'CC1\0'; MAX_TOTAL=64*1024*1024; MAX_MANIFEST=8*1024*1024
MAX_FILES=4096; MAX_OBJECTS=32768; MAX_CHUNK=16384; MAX_WIRE=MAX_TOTAL+MAX_MANIFEST+MAX_OBJECTS*64
H=struct.Struct('<4sII'); R=struct.Struct('<32sI'); U=struct.Struct('<I')
GEAR=[int.from_bytes(hashlib.sha256(bytes([i])).digest()[:8],'little') for i in range(256)]
class Error(ValueError): pass
def need(ok,msg):
    if not ok: raise Error(msg)
def digest(b): return hashlib.sha256(b).hexdigest()
def canon(x): return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
def inflate(b,cap):
    try:
        d=zlib.decompressobj(); x=d.decompress(b,cap+1)
        need(len(x)<=cap and d.eof and not d.unconsumed_tail and not d.unused_data,'bad compressed data'); return x
    except zlib.error as e: raise Error('invalid deflate') from e
def read_limited(p,cap):
    with open(p,'rb') as f: b=f.read(cap+1)
    need(len(b)<=cap,'input limit'); return b
def valid_hash(h): return isinstance(h,str) and bool(re.fullmatch('[0-9a-f]{64}',h))
def valid_path(p):
    if not isinstance(p,str) or not 0<len(p)<=1024: return False
    for s in p.split('/'):
        if not s or s in ('.','..') or len(s.encode('utf-8'))>255 or s[-1] in ' .' or any(ord(c)<32 or c in '\\:<>"|?*' for c in s): return False
        if re.fullmatch(r'(?i:CON|PRN|AUX|NUL|COM[1-9¹²³]|LPT[1-9¹²³])',s.split('.')[0]): return False
    return True

def chunks(b,mode='cdc'):
    if mode=='fixed':
        yield from (b[i:i+8192] for i in range(0,len(b),8192)); return
    need(mode=='cdc','unknown chunker'); start=state=0
    for i,v in enumerate(b,1):
        state=((state<<1)+GEAR[v])&0xffffffffffffffff; n=i-start
        if n>=2048 and ((state&8191)==0 or n>=MAX_CHUNK):
            yield b[start:i]; start=i; state=0
    if start<len(b): yield b[start:]

def snapshot(root,mode='cdc'):
    root=Path(root); need(root.is_dir() and not root.is_symlink(),'source must be a real directory')
    files=[]; dirs=[]; objects={}; total=0
    for base,ds,fs in os.walk(root,followlinks=False):
        ds.sort(); fs.sort()
        for name in ds:
            p=Path(base)/name; need(not p.is_symlink(),'symlink unsupported'); dirs.append(p.relative_to(root).as_posix())
        for name in fs:
            p=Path(base)/name; need(p.is_file() and not p.is_symlink(),'special file unsupported')
            b=read_limited(p,MAX_TOTAL-total); total+=len(b); refs=[]
            for x in chunks(b,mode):
                h=digest(x); objects[h]=x; refs.append(h)
            files.append({'path':p.relative_to(root).as_posix(),'size':len(b),'sha256':digest(b),'chunks':refs})
    m={'version':1,'dirs':sorted(dirs),'files':sorted(files,key=lambda f:f['path'])}; validate(m); return m,objects

def validate(m):
    need(isinstance(m,dict) and set(m)=={'version','dirs','files'} and type(m['version']) is int and m['version']==1,'manifest schema')
    ds,fs=m['dirs'],m['files']; need(isinstance(ds,list) and isinstance(fs,list) and len(ds)+len(fs)<=MAX_FILES,'entry limit')
    paths=set(); folded=set(); total=refs=0
    for p in ds+[f.get('path') if isinstance(f,dict) else None for f in fs]:
        need(valid_path(p),'invalid path'); need(p.casefold() not in folded,'duplicate/case-colliding path'); paths.add(p); folded.add(p.casefold())
    dset=set(ds)
    for p in paths: need('/' not in p or p.rsplit('/',1)[0] in dset,'missing parent directory')
    for f in fs:
        need(isinstance(f,dict) and set(f)=={'path','size','sha256','chunks'},'file schema')
        n=f['size']; cs=f['chunks']; need(type(n) is int and 0<=n<=MAX_TOTAL and valid_hash(f['sha256']) and isinstance(cs,list),'file metadata')
        need(all(valid_hash(h) for h in cs) and (bool(cs)==bool(n)),'chunk references'); total+=n; refs+=len(cs)
    need(total<=MAX_TOTAL and refs<=MAX_OBJECTS,'manifest resource limit')
    return {h for f in fs for h in f['chunks']}

def object_encode(b,engine='deflate'):
    choices=[b'\0'+b,b'\1'+zlib.compress(b,9)]
    if engine=='ec1': choices.append(b'\2'+ec1.encode([b])[0])
    else: need(engine=='deflate','unknown engine')
    return min(choices,key=lambda x:(len(x),x))
def object_decode(p):
    need(0<len(p)<=MAX_CHUNK+1,'object payload bound'); t=p[0]
    if t==0: b=p[1:]
    elif t==1: b=inflate(p[1:],MAX_CHUNK)
    elif t==2:
        # Bound EC1 record count and source size before invoking its decoder.
        need(len(p)>=1+ec1.HEADER.size+ec1.RECORD.size,'EC1 object header')
        magic,count=ec1.HEADER.unpack_from(p,1); tag,n,k,_=ec1.RECORD.unpack_from(p,1+ec1.HEADER.size)
        need(magic==ec1.MAGIC and count==1 and n<=MAX_CHUNK,'EC1 object bounds')
        try: b=ec1.decode(p[1:])[0]
        except ec1.FormatError as e: raise Error('bad EC1 object') from e
    else: raise Error('unknown object mode')
    need(0<len(b)<=MAX_CHUNK,'object size'); return b

def make_bundle(m,objects,known=(),engine='deflate'):
    refs=validate(m); known=set(known); missing=sorted(refs-known)
    raw=canon(m); need(len(raw)<=MAX_MANIFEST,'manifest too large'); meta=zlib.compress(raw,9)
    parts=[H.pack(MAGIC,len(meta),len(missing)),meta]
    for h in missing:
        b=objects[h]; need(digest(b)==h,'source object mismatch'); p=object_encode(b,engine)
        parts.extend((R.pack(bytes.fromhex(h),len(p)),p))
    out=b''.join(parts); need(len(out)<=MAX_WIRE,'wire limit'); return out

def parse_bundle(wire):
    need(H.size<=len(wire)<=MAX_WIRE,'bundle bounds'); magic,n,count=H.unpack_from(wire)
    need(magic==MAGIC and n<=len(wire)-H.size and count<=MAX_OBJECTS,'bundle header')
    i=H.size+n
    try: m=json.loads(inflate(wire[H.size:i],MAX_MANIFEST))
    except (ValueError,UnicodeError,RecursionError) as e: raise Error('bad manifest') from e
    refs=validate(m); objects={}; total=0
    for _ in range(count):
        need(i+R.size<=len(wire),'truncated object header'); h,k=R.unpack_from(wire,i); i+=R.size; h=h.hex()
        need(h in refs and h not in objects and k<=MAX_CHUNK+1 and k<=len(wire)-i,'object record bounds')
        b=object_decode(wire[i:i+k]); i+=k; total+=len(b); need(total<=MAX_TOTAL,'decoded object limit'); need(digest(b)==h,'object digest mismatch'); objects[h]=b
    need(i==len(wire),'trailing bundle data'); return m,objects

def inventory(store):
    store=Path(store); result=[]
    if not store.exists(): return result
    need(store.is_dir() and not store.is_symlink(),'invalid store')
    for p in sorted(store.iterdir()):
        if valid_hash(p.name) and p.is_file() and not p.is_symlink():
            try:
                if digest(object_decode(read_limited(p,MAX_CHUNK+1)))==p.name: result.append(p.name)
            except (OSError,Error): pass
    need(len(result)<=MAX_OBJECTS,'inventory limit'); return result

def inventory_wire(hashes):
    hs=sorted(set(hashes)); need(len(hs)<=MAX_OBJECTS and all(valid_hash(h) for h in hs),'bad inventory'); return U.pack(len(hs))+b''.join(bytes.fromhex(h) for h in hs)
def parse_inventory(b):
    need(len(b)>=4,'inventory header'); n=U.unpack_from(b)[0]; need(n<=MAX_OBJECTS and len(b)==4+32*n,'inventory length'); hs=[b[i:i+32].hex() for i in range(4,len(b),32)]; need(hs==sorted(set(hs)),'noncanonical inventory'); return hs

def receive(wire,store,destination):
    m,incoming=parse_bundle(wire); refs=validate(m); store=Path(store); dest=Path(destination)
    need(not dest.exists() and not dest.is_symlink(),'destination already exists')
    need(not store.is_symlink(),'invalid store'); store.mkdir(parents=True,exist_ok=True)
    all_objects=dict(incoming); total_objects=sum(map(len,incoming.values()))
    for h in refs-incoming.keys():
        p=store/h; need(p.is_file() and not p.is_symlink(),'missing historical object')
        b=object_decode(read_limited(p,MAX_CHUNK+1)); total_objects+=len(b); need(total_objects<=MAX_TOTAL,'decoded object limit'); need(digest(b)==h,'stored object digest mismatch'); all_objects[h]=b
    # Verify every file before materializing it; no path is taken from the object store.
    total=0
    for f in m['files']:
        n=sum(len(all_objects[h]) for h in f['chunks']); need(n==f['size'],'file size mismatch'); total+=n; need(total<=MAX_TOTAL,'output limit')
        hash=hashlib.sha256()
        for h in f['chunks']: hash.update(all_objects[h])
        need(hash.hexdigest()==f['sha256'],'file digest mismatch')
    # New destination only; previous snapshots are never mutated or deleted.
    dest.mkdir(parents=False)
    try:
        for p in sorted(m['dirs'],key=lambda x:(x.count('/'),x)): (dest/p).mkdir()
        for f in m['files']:
            with open(dest/f['path'],'xb') as stream:
                for h in f['chunks']: stream.write(all_objects[h])
        for h,b in incoming.items():
            p=store/h; need(not p.is_symlink(),'invalid store object path')
            fd,tmp=tempfile.mkstemp(dir=store)
            try:
                with os.fdopen(fd,'wb') as f: f.write(object_encode(b))
                os.replace(tmp,p)
            finally:
                if os.path.exists(tmp): os.unlink(tmp)
    except BaseException:
        shutil.rmtree(dest); raise
    return {'snapshot_sha256':digest(canon(m)),'files':len(m['files']),'received_objects':len(incoming),'reused_objects':len(refs-incoming.keys())}

def main():
    p=argparse.ArgumentParser(description='CC1 experimental directory snapshot transfer'); sub=p.add_subparsers(dest='cmd',required=True)
    q=sub.add_parser('pack'); q.add_argument('source'); q.add_argument('bundle'); q.add_argument('--inventory'); q.add_argument('--chunker',choices=['fixed','cdc'],default='cdc'); q.add_argument('--engine',choices=['deflate','ec1'],default='deflate')
    q=sub.add_parser('inventory'); q.add_argument('store'); q.add_argument('output')
    q=sub.add_parser('restore'); q.add_argument('bundle'); q.add_argument('store'); q.add_argument('destination')
    q=sub.add_parser('inspect'); q.add_argument('bundle')
    a=p.parse_args()
    try:
        if a.cmd=='pack':
            m,o=snapshot(a.source,a.chunker); known=parse_inventory(read_limited(a.inventory,4+32*MAX_OBJECTS)) if a.inventory else []; wire=make_bundle(m,o,known,a.engine)
            with open(a.bundle,'xb') as f:f.write(wire)
            print(json.dumps({'snapshot_sha256':digest(canon(m)),'bytes':len(wire),'files':len(m['files'])}))
        elif a.cmd=='inventory':
            b=inventory_wire(inventory(a.store))
            with open(a.output,'xb') as f:f.write(b)
            print(json.dumps({'inventory_bytes':len(b)}))
        elif a.cmd=='restore': print(json.dumps(receive(read_limited(a.bundle,MAX_WIRE),a.store,a.destination)))
        else:
            m,o=parse_bundle(read_limited(a.bundle,MAX_WIRE)); print(json.dumps({'manifest':m,'included_objects':len(o),'external_objects':len(validate(m)-o.keys())},indent=2))
    except (OSError,Error,UnicodeError,KeyError) as e: p.exit(2,f'CC1: {e}\n')
if __name__=='__main__': main()
