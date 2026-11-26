"""HV1 local workbench: capture, observe, plan, assent, restore. Trusted local paths only."""
import argparse,json,os,tempfile,time
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import circulation as c, commonwealth as cw, sensation as sn, interdependence as id1, covenant as cv

def read(p,cap=c.MAX_MANIFEST):return json.loads(c.read_limited(p,cap))
def write(p,x):
    with open(p,'xb') as f:f.write(c.canon(x)+b'\n')
def pin(x):return c.digest(c.canon(x))
def real(p):
    p=Path(p).absolute();c.need(not any(x.is_symlink() for x in (p,*p.parents)),'symlink path component');return p.resolve()
def disjoint(paths):
    pp=[real(p) for p in paths];c.need(all(a!=b and a not in b.parents and b not in a.parents for i,a in enumerate(pp) for b in pp[i+1:]),'overlapping paths');return pp

def capture(src,out):
    src,out=disjoint([src,out]);c.need(not out.exists() and out.parent.is_dir(),'new capture directory required')
    m,obj=c.snapshot(src);out.mkdir();(out/'objects').mkdir();write(out/'manifest.json',m)
    for h,b in obj.items():cw.save_object(out/'objects',h,b)
    receipt=dict(schema='HV1-capture',manifest_pin=pin(m),files=len(m['files']),objects=len(obj));write(out/'capture.json',receipt);return receipt

def field(m,mp,peers,records=None,rp=None):
    c.need(c.valid_hash(mp) and pin(m)==mp,'manifest pin');c.validate(m)
    c.need(isinstance(peers,dict) and 1<=len(peers)<=32 and all(cv.ident(k) and k!='destination' for k in peers),'peer labels')
    pp=disjoint(peers.values());peers=dict(zip(peers,map(str,pp)))
    c.need((records is None)==(rp is None),'equation pin required')
    if records is not None:c.need(c.valid_hash(rp) and pin(records)==rp,'equation pin')
    return peers,sn.observe(m,mp,peers,records=records,record_pin=rp)

def trust_check(trust,tp,peers):
    c.need(isinstance(trust,dict) and set(trust)==set(peers)|{'destination'} and all(cv.hexstr(k,64) for k in trust.values()) and pin(trust)==tp,'trusted roster pin or roles')

def plan(m,mp,peers,dest,trust,tp,records=None,rp=None):
    peers,report=field(m,mp,peers,records,rp);trust_check(trust,tp,peers);dest=disjoint([*peers.values(),dest])[-1]
    c.need(not dest.exists() and dest.parent.is_dir(),'fresh destination required')
    states={k:{'root':r['root_status'],'objects':{h:v['status'] for h,v in r['observations'].items()}} for k,r in report['peers'].items()}
    required=set(c.validate(m));derived=set(report['regenerated_in_memory']);source={};loads={k:0 for k in peers}
    # Only verified objects, and only parity if a direct object is missing.
    wanted=set(report['verified_union'])| (set(report['verified_parity']) if required-set(report['verified_union']) else set())
    for h in sorted(wanted):
        k=min((k for k,r in states.items() if r['objects'].get(h)=='verified'),key=lambda k:(loads[k],k));source[h]=k;loads[k]+=1
    ready=not report['not_verified'] and not report['solver_error'] and report['verified_files_from_observed_union']==len(m['files'])
    return dict(schema='HV1-plan',manifest_pin=mp,record_pin=rp,trust_pin=tp,peers=peers,destination=str(dest),observation_pin=pin(states),sources=source,derived=sorted(derived),missing=sorted(required-set(source)-derived),status='ready' if ready else 'blocked',required_signers=sorted({trust[k] for k in set(source.values())|{'destination'}}))

def assent(key,p,until,now):
    c.need(p['status']=='ready' and cv.key(key) in p['required_signers'] and cv.integer(now,0,2**53-1) and cv.integer(until,now+1,2**53-1),'approval scope or time')
    return cv.signed(key,dict(issuer=cv.key(key),plan=pin(p),at=now,until=until),'hv-assent')

def restore(m,mp,p,trust,tp,approvals,now,records=None,rp=None):
    # Reject stale plan and missing approvals before creating any destination.
    c.need(p==plan(m,mp,p['peers'],p['destination'],trust,tp,records,rp) and p['status']=='ready','stale or blocked plan')
    need=set(p['required_signers']);seen=set()
    c.need(isinstance(approvals,list) and len(approvals)==len(need) and cv.integer(now,0,2**53-1),'assent count/time')
    for a in approvals:
        b=cv.check(a,'hv-assent');cv.shape(b,'issuer plan at until');c.need(b['issuer'] in need-seen and b['plan']==pin(p) and cv.integer(b['at'],0,now) and cv.integer(b['until'],now+1,2**53-1),'invalid assent');seen.add(b['issuer'])
    refs=c.validate(m);known={};parity={}
    for h,k in p['sources'].items():
        row,b=sn.probe(Path(p['peers'][k]),h);c.need(row['status']=='verified' and b is not None,'source changed');(known if h in refs else parity)[h]=b
        # A parity object can itself be an ordinary content chunk.
        if records is not None and any(r['parity']==h for r in records):parity[h]=b
    direct=set(known)
    if refs-direct:
        c.need(records is not None,'missing objects');known=id1.solve(refs,records,known,parity)
    c.need(set(known)==refs and sorted(refs-direct)==p['derived'],'recovery differs from plan')
    dest=Path(p['destination'])
    with tempfile.TemporaryDirectory(prefix='hv-cache-') as tmp:
        result=c.receive(c.make_bundle(m,known),Path(tmp)/'objects',dest)
    # Independently read back restored files, without depending on chunker choice.
    mm,_=c.snapshot(dest);c.need(mm['dirs']==m['dirs'] and [(f['path'],f['size'],f['sha256']) for f in mm['files']]==[(f['path'],f['size'],f['sha256']) for f in m['files']],'output verification failed')
    return dict(schema='HV1-restored',plan_pin=pin(p),manifest_pin=mp,approval_ids=sorted(pin(a) for a in approvals),direct=len(direct),regenerated=len(refs-direct),destination=str(dest),verified_files=result['files'])

def main():
    a=argparse.ArgumentParser(description=__doc__);s=a.add_subparsers(dest='cmd',required=True)
    q=s.add_parser('capture');q.add_argument('source');q.add_argument('out')
    q=s.add_parser('keygen');q.add_argument('private_file')
    q=s.add_parser('hash');q.add_argument('json_file')
    for cmd in ('observe','plan','restore'):
        q=s.add_parser(cmd);q.add_argument('manifest');q.add_argument('manifest_pin');q.add_argument('--equations');q.add_argument('--equation-pin')
        if cmd!='restore':q.add_argument('--peer',action='append',required=True,help='LABEL=PATH')
        if cmd!='observe':q.add_argument('--trust',required=True);q.add_argument('--trust-pin',required=True)
        if cmd=='plan':q.add_argument('destination');q.add_argument('output')
        if cmd=='restore':q.add_argument('plan_file');q.add_argument('--assent',action='append',required=True)
    q=s.add_parser('approve');q.add_argument('plan_file');q.add_argument('private_file');q.add_argument('output');q.add_argument('--ttl',type=int,default=3600)
    q=s.add_parser('demo');q.add_argument('directory')
    z=a.parse_args();now=int(time.time())
    try:
        if z.cmd=='capture':r=capture(z.source,z.out)
        elif z.cmd=='keygen':
            k=Ed25519PrivateKey.generate();fd=os.open(z.private_file,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            with os.fdopen(fd,'wb') as f:f.write(k.private_bytes_raw())
            r={'public_key':cv.key(k)}
        elif z.cmd=='hash':r={'pin':pin(read(z.json_file))}
        elif z.cmd=='approve':
            c.need(1<=z.ttl<=86400,'TTL range');k=Ed25519PrivateKey.from_private_bytes(c.read_limited(z.private_file,32));p=read(z.plan_file);r=assent(k,p,now+z.ttl,now);write(z.output,r)
        elif z.cmd=='demo':
            from demo import run
            r=run(z.directory)
        else:
            m=read(z.manifest);records=read(z.equations) if z.equations else None;rp=z.equation_pin
            if z.cmd!='restore':
                pairs=[x.split('=',1) for x in z.peer];peers=dict(pairs);c.need(len(peers)==len(pairs),'duplicate peer')
            if z.cmd=='observe':_,r=field(m,z.manifest_pin,peers,records,rp)
            elif z.cmd=='plan':r=plan(m,z.manifest_pin,peers,z.destination,read(z.trust),z.trust_pin,records,rp);write(z.output,r)
            else:r=restore(m,z.manifest_pin,read(z.plan_file),read(z.trust),z.trust_pin,[read(f) for f in z.assent],now,records,rp)
        print(json.dumps(r,indent=2))
        if r.get('status')=='blocked':return 3
        return 0
    except (ValueError,OSError,TypeError,KeyError,IndexError,RecursionError) as e:print('HV1:',e,file=__import__('sys').stderr);return 2
if __name__=='__main__':raise SystemExit(main())
