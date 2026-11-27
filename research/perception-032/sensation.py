"""Read-only CC1 store observation. No repairs or network probing."""
import argparse, datetime, hashlib, json, os, stat, time, shutil
from pathlib import Path
from collections import Counter
import circulation as c
import interdependence as d

MAX_PEERS=32
MAX_OBSERVATIONS=100000
STATES=('verified','missing','corrupt','unsafe','unknown','unobserved','named')
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def identity(s):return (s.st_dev,s.st_ino)
def version(s):return (identity(s),s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def probe(root,h,metadata=False):
    start=time.perf_counter_ns();n=0;payload=None;seen=False
    def done(status,reason):return {'status':status,'reason':reason,'read_bytes':n,'elapsed_ns':time.perf_counter_ns()-start},payload
    p=root/h
    try:
        a=p.lstat();seen=True
        if not stat.S_ISREG(a.st_mode):return done('unsafe','not_regular')
        if metadata:return done('named','not_hash_verified')
        if a.st_size>c.MAX_CHUNK+1:return done('corrupt','oversized')
        flags=os.O_RDONLY|getattr(os,'O_BINARY',0)|getattr(os,'O_NOFOLLOW',0)|getattr(os,'O_NONBLOCK',0)
        fd=os.open(p,flags)
        with os.fdopen(fd,'rb') as f:
            b=os.fstat(f.fileno())
            if not stat.S_ISREG(b.st_mode) or version(a)!=version(b):return done('unknown','changed_before_read')
            wire=f.read(c.MAX_CHUNK+2);n=len(wire)
            if version(b)!=version(os.fstat(f.fileno())) or version(b)!=version(p.lstat()):return done('unknown','changed_during_read')
        try:
            raw=c.object_decode(wire)
            if c.digest(raw)!=h:return done('corrupt','digest_mismatch')
        except (ValueError,UnicodeError):return done('corrupt','invalid_encoding')
        payload=raw;return done('verified','sha256_match')
    except FileNotFoundError:
        return done('missing' if not seen else 'unknown','not_found' if not seen else 'changed_after_lookup')
    except OSError as e:return done('unknown',type(e).__name__)

def select(refs,limit,seed):
    return sorted(sorted(refs,key=lambda h:hashlib.sha256((str(seed)+':'+h).encode()).digest())[:limit])

def observe(m,pin,peers,limit=None,seed=0,metadata=False,records=None,record_pin=None,selection=None):
    refs=sorted(c.validate(m));c.need(c.digest(c.canon(m))==pin,'manifest pin mismatch')
    c.need(0<len(peers)<=MAX_PEERS and len({str(Path(p).resolve()) for p in peers.values()})==len(peers),'distinct peers required')
    c.need(limit is None or 0<=limit<=c.MAX_OBJECTS,'sample limit')
    ph=set()
    if records is not None:
        c.need(not metadata and isinstance(records,list) and len(records)<=d.MAX_ROWS and len(refs)<=d.MAX_VARS,'equation bounds or metadata mode')
        c.need(c.digest(c.canon(records))==record_pin,'equation pin mismatch')
        for r in records:
            c.need(set(d.validate(r))<=set(refs),'unknown equation member');ph.add(r['parity'])
    sample=select(sorted(set(refs)|ph),len(set(refs)|ph) if limit is None else limit,seed) if selection is None else sorted(selection)
    c.need(len(sample)==len(set(sample)) and set(sample)<=set(refs)|ph,'invalid explicit selection')
    rows={};union=set();all_data={};started=stamp();t=time.perf_counter_ns()
    c.need(len(sample)*len(peers)<=MAX_OBSERVATIONS,'observation count limit; use sampling')
    for label,path in sorted(peers.items()):
        root=Path(path);begin=time.perf_counter_ns();obs={};data={};capacity=None;status='accessible'
        try:
            a=root.lstat();c.need(stat.S_ISDIR(a.st_mode),'root not a real directory')
            try:
                v=os.statvfs(root);capacity={'filesystem_id':str(a.st_dev),'total_bytes':v.f_blocks*v.f_frsize,'available_bytes':v.f_bavail*v.f_frsize}
            except (AttributeError,OSError):
                try:
                    v=shutil.disk_usage(root);capacity={'filesystem_id':str(a.st_dev),'total_bytes':v.total,'available_bytes':v.free}
                except OSError:pass
            for h in sample:
                obs[h],b=probe(root,h,metadata)
                if b is not None:data[h]=b
            if identity(root.lstat())!=identity(a) or not stat.S_ISDIR(root.lstat().st_mode):raise OSError('root changed')
        except (OSError,c.Error) as e:
            status='unavailable';capacity=None;data={}
            obs={h:{'status':'unknown','reason':type(e).__name__,'read_bytes':v.get('read_bytes',0),'elapsed_ns':v.get('elapsed_ns',0)} for h in sample for v in [obs.get(h,{})]}
        counts=Counter(v['status'] for v in obs.values());counts['unobserved']=len(set(refs)|ph)-len(sample)
        union.update(data);all_data.update(data)
        rows[label]={'root_status':status,'capacity':capacity,'counts':{s:counts[s] for s in STATES},'observations':obs,'elapsed_ns':time.perf_counter_ns()-begin,'read_bytes':sum(v['read_bytes'] for v in obs.values())}
    direct=set(refs)&union;derived=set();solver_error=None
    if records is not None:
        try:
            solved=d.solve(set(refs),records,{h:all_data[h] for h in direct},{h:all_data[h] for h in ph&union})
            derived=set(solved)-direct;all_data.update(solved)
        except c.Error as e:solver_error=str(e)
    files=0
    for f in m['files']:
        if not metadata and all(h in all_data for h in f['chunks']):
            n=sum(len(all_data[h]) for h in f['chunks'])
            if n==f['size']:
                sha=hashlib.sha256()
                for h in f['chunks']:sha.update(all_data[h])
                if sha.hexdigest()==f['sha256']:files+=1
    return {'schema':'SN1','manifest_pin':pin,'record_pin':record_pin,'started_utc':started,'finished_utc':stamp(),'mode':'metadata' if metadata else 'verify','sample_seed':seed,'required_objects':len(refs),'sampled_objects':len(set(sample)&set(refs)),'sampled_parity':len(set(sample)&ph),'parity_objects':len(ph),'required_files':len(m['files']),'verified_files_from_observed_union':files,'verified_union':sorted(direct),'regenerated_in_memory':sorted(derived),'verified_parity':sorted(ph&union),'solver_error':solver_error,'not_verified':len(refs)-len(direct|derived),'elapsed_ns':time.perf_counter_ns()-t,'peers':rows}

def compare(previous,current):
    c.need(previous['manifest_pin']==current['manifest_pin'] and previous.get('record_pin')==current.get('record_pin'),'different manifests or equations')
    out={}
    for p,row in current['peers'].items():
        old=previous['peers'].get(p,{}).get('observations',{});changes=Counter()
        for h,v in row['observations'].items():
            a=old.get(h,{}).get('status','unobserved');b=v['status']
            if a!=b:changes[a+' -> '+b]+=1
        out[p]=dict(changes)
    return out

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest');p.add_argument('pin');p.add_argument('--peer',action='append',required=True,help='LABEL=PATH');p.add_argument('--sample',type=int);p.add_argument('--seed',type=int,default=0);p.add_argument('--metadata-only',action='store_true');p.add_argument('--previous');p.add_argument('--records');p.add_argument('--record-pin');p.add_argument('--selection',help='PN1 report specifying next selection');a=p.parse_args()
    try:
        pairs=[v.split('=',1) for v in a.peer];peers=dict(pairs);c.need(len(peers)==len(pairs) and all(peers),'duplicate or empty label')
        m=json.loads(c.read_limited(a.manifest,c.MAX_MANIFEST));c.need(bool(a.records)==bool(a.record_pin),'records and record pin required together')
        records=json.loads(c.read_limited(a.records,c.MAX_MANIFEST)) if a.records else None
        selection=None
        if a.selection:
            plan=json.loads(c.read_limited(a.selection,64*1024*1024));c.need(plan['schema']=='PN1' and plan['manifest_pin']==a.pin and a.sample is None,'selection identity or conflicting sample');selection=plan['next_selection']
        r=observe(m,a.pin,peers,a.sample,a.seed,a.metadata_only,records,a.record_pin,selection)
        if a.previous:r['transitions']=compare(json.loads(c.read_limited(a.previous,64*1024*1024)),r)
        print(json.dumps(r,indent=2))
    except (OSError,ValueError,TypeError,KeyError,RecursionError) as e:p.exit(2,f'SN1: {e}\n')
if __name__=='__main__':main()
