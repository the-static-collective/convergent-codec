"""Crossroads 010: trusted local research compiler, standard library only."""
import argparse, hashlib, json, os, tempfile, zlib, math, statistics
from pathlib import Path
import genesis as G
import living as L
import conservation as C
import sufficiency as S
ROOT=Path(__file__).resolve().parent
SCHEMA='crossroads.compiler/v1'; MAX_ACTIVE=8; MAX_POOL=4096

def canonical(obj):return json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
def digest(obj):return hashlib.sha256(canonical(obj)).hexdigest()
def atomic(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as f:f.write(canonical(obj)+b'\n');f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
def load(path):return json.loads(Path(path).read_text())
def check(ok,msg):
    if not ok:raise ValueError(msg)
def state_init(seed=True):
    c=load(ROOT/'catalog.json'); roots=c['roots'] if seed else ['00']; parents=sorted(set(roots+(c['parents']+c['exact_stage2'] if seed else [])))
    return {'schema':SCHEMA,'seed':{'mode':'genesis-reviewed-subset' if seed else 'length-only','catalog_sha256':digest(c),'eligible':parents},'events':[]}
def entries(state):
    check(state.get('schema')==SCHEMA,'state schema');c=load(ROOT/'catalog.json');check(state['seed']['catalog_sha256']==digest(c),'seed catalog mismatch'); check(state['seed']==state_init(state['seed']['mode']=='genesis-reviewed-subset')['seed'],'seed mismatch')
    rows={h:{'uses':0,'yield_bytes':0,'last':-1,'origin':'Genesis seed'} for h in state['seed']['eligible']};prev=digest(state['seed'])
    for i,e in enumerate(state['events']):
        check(e['index']==i and e['prev']==prev and digest({k:v for k,v in e.items() if k!='hash'})==e['hash'],'journal chain mismatch')
        prev=e['hash'];h=e['admitted'];
        if h:
            check(h==e['selected'],'admission mismatch');rows.setdefault(h,{'uses':0,'yield_bytes':0,'last':-1,'origin':e['hash']})
        if e['used'] and e['used'] in rows:
            q=rows[e['used']];q['uses']+=1;q['yield_bytes']+=e['target_saved'];q['last']=i
    return rows,prev

def active(rows):
    return sorted(rows,key=lambda h:(-rows[h]['last'],-rows[h]['yield_bytes'],len(h),h))[:MAX_ACTIVE]
def bank_ok(xs,ys):
    check(isinstance(xs,list) and 1<=len(xs)<=256 and isinstance(ys,list) and len(xs)==len(ys),'bank size')
    for x in xs:check(isinstance(x,list) and 1<=len(x)<=8 and all(type(v)==int and abs(v)<=32 for v in x),'input domain')
    check(all(type(y)==int and abs(y)<2**63 for y in ys),'output domain')
def inputs_ok(xs):bank_ok(xs,[0]*len(xs))
def safe_expr(e):
    t,p=G.parse(e);check(p==len(e) and len(e)<=31,'expression bounds');return e

def decode(f,xs):
    # GE1 compatible decoder, explicit checks instead of assertions; bounded expansion.
    inputs_ok(xs);check(69<=len(f)<=65536,'frame size');r=L.Reader(f[:-32]);check(r.take(3)==b'GE1','header');n=r.u();check(n==len(xs) and r.take(32)==L.input_hash(xs),'input context');mode=r.take(1);p=r.take(len(r.b)-r.p)
    if mode in (b'Z',b'H'):
        z=zlib.decompressobj();p=z.decompress(p,65536);check(z.eof and not z.unused_data and not z.unconsumed_tail,'compressed payload')
    r=L.Reader(p)
    if mode in (b'R',b'Z'):ys=[r.s() for _ in xs]
    elif mode in (b'M',b'H'):
        e=safe_expr(r.take(r.u()));base=[G.evaluate(e,x) for x in xs];tag=r.take(1);rr=[0]*n
        if tag==b'\0':rr=[r.s() for _ in xs]
        elif tag==b'\1':
            c=r.u();check(c<=n,'residual count');last=-1
            for _ in range(c):
                j,v=r.u(),r.s();check(last<j<n and v!=0,'residual position');rr[j]=v;last=j
        else:raise ValueError('residual mode')
        ys=[a+b for a,b in zip(base,rr)]
    else:raise ValueError('mode')
    r.done();bank_ok(xs,ys);check(hashlib.sha256(L.raw([ys])).digest()==f[-32:],'output digest');return ys

def pool(roots,parents=()):
    out=[]
    for e in G.pool(roots,parents):
        try:safe_expr(e)
        except ValueError:continue
        out.append(e)
    check(len(out)<=MAX_POOL,'candidate budget exceeded');return out

def select(xs,ys,es):
    q=C.quotient(es);best=None;count=0;skipped=0
    for e in q:
        v=[G.evaluate(e,x) for x in xs];count+=1
        if any(abs(z).bit_length()>115 for z in v):skipped+=1;continue
        rr=[a-b for a,b in zip(ys,v)];score=(len(L.u(len(e)))+len(e)+len(L.residual(rr)),len(e),e)
        if best is None or score<best:best=score
    return (best[2] if best else None),{'enumerated':len(es),'representatives':len(q),'evaluations':count,'oversized_skipped':skipped}
def evaluate_safe(e,xs):
    if e is None:return None
    v=[G.evaluate(e,x) for x in xs];return v if all(abs(z).bit_length()<=115 for z in v) else None

def fit(state,request,allow_learning=True,escalate=True,sufficiency=False):
    rows,prev=entries(state)
    for k in ('train','validate','target'):bank_ok(request[k]['inputs'],request[k]['outputs'])
    train,val,target=(request[k] for k in ('train','validate','target'));check(not ({tuple(x) for x in train['inputs']}&{tuple(x) for x in val['inputs']}),'train/validation overlap');check(not ({tuple(x) for k in ('train','validate') for x in request[k]['inputs']}&{tuple(x) for x in target['inputs']}),'calibration/target overlap')
    a=[bytes.fromhex(h) for h in active(rows)];known=[bytes.fromhex(h) for h in rows];atoms=[bytes([i]) for i in range(len(G.ATOMS))]
    report=S.assess(train,val) if sufficiency else None
    held=report is not None and report['search']=='HOLD'
    budget=False
    def exact(e,data):return evaluate_safe(e,data['inputs'])==data['outputs']
    if held:
        e=None;stages=[]
    else:
        e,m=select(train['inputs'],train['outputs'],a);stages=[{'stage':'active',**m}]
        if not exact(e,train):
            e,m=select(train['inputs'],train['outputs'],known);stages.append({'stage':'archive',**m})
        if escalate and not exact(e,train):
            try:
                candidates=pool(atoms,known)
            except ValueError as exc:
                if not sufficiency or str(exc)!='candidate budget exceeded':raise
                budget=True
            else:
                e,m=select(train['inputs'],train['outputs'],candidates);stages.append({'stage':'compose',**m})
    vx,vy=val['inputs'],val['outputs'];valid=exact(e,val);train_exact=exact(e,train);base_v=G.wire(vx,vy);vframe=G.wire(vx,vy,e if evaluate_safe(e,vx) is not None else None)
    h=e.hex() if e else None;admit=h if allow_learning and train_exact and valid and h not in rows and len(vframe)<len(base_v) and len(rows)<64 else None
    # Candidate fixed before target outputs used. Unvalidated models not used to encode target.
    tx,ty=target['inputs'],target['outputs'];pred=evaluate_safe(e,tx) if valid else None;baseline=G.wire(tx,ty);frame=G.wire(tx,ty,e if pred is not None else None);check(decode(frame,tx)==ty,'round trip')
    mode=chr(frame[3+len(L.u(len(tx)))+32]);residuals=[[i,y-p] for i,(y,p) in enumerate(zip(ty,pred)) if y!=p] if pred is not None else None
    calibration_bytes=len(zlib.compress(canonical({'train':train,'validate':val}),9));context_bytes=len(zlib.compress(canonical(tx),9)); artifact={'schema':'crossroads.artifact/v1','policy':{'allow_learning':allow_learning,'escalate':escalate},'name':request.get('name','encounter'),'source':request.get('source','user supplied; unverified'),'request':request,'frame':frame.hex(),'baseline_frame':baseline.hex(),'selected':h,'expression':G.pretty(e) if e else None,'train_exact':train_exact,'validation_exact':valid,'admitted':admit,'mode':mode,'prediction_exact':sum(y==p for y,p in zip(ty,pred)) if pred is not None else 0,'target_count':len(ty),'residuals':residuals,'stages':stages,'accounting':{'wire':len(frame),'baseline':len(baseline),'saved':len(baseline)-len(frame),'calibration_zlib_bytes':calibration_bytes,'context_zlib_bytes':context_bytes,'definition_bytes':len(e) if e else 0,'validation_saved':len(base_v)-len(vframe)}}
    if sufficiency:
        artifact['policy']['sufficiency']=True
        artifact['sufficiency']={**report,'resolution':S.classify(report,train_exact,valid,any(q['stage']=='compose' for q in stages),admit,budget)}
    event={'index':len(state['events']),'prev':prev,'artifact':digest(artifact),'selected':h,'admitted':admit,'used':h if mode in 'MH' else None,'target_saved':len(baseline)-len(frame),'active_before':active(rows),'train_exact':train_exact,'validation_exact':valid,'stages':stages};event['hash']=digest(event);return artifact,event

def compile_file(state_path,request,artifact_dir,**kw):
    state=load(state_path);artifact,event=fit(state,request,**kw);dest=Path(artifact_dir)/(event['artifact']+'.json');atomic(dest,artifact);state['events'].append(event);atomic(state_path,state);return artifact,event

def verify(state_path,artifact_dir):
    state=load(state_path);rows,head=entries(state);replay={'schema':state['schema'],'seed':state['seed'],'events':[]}
    for e in state['events']:
        a=load(Path(artifact_dir)/(e['artifact']+'.json'));check(digest(a)==e['artifact'],'artifact hash');t=a['request']['target'];check(decode(bytes.fromhex(a['frame']),t['inputs'])==t['outputs'],'artifact data');check(decode(bytes.fromhex(a['baseline_frame']),t['inputs'])==t['outputs'],'baseline data')
        # Replay exact policy; flags recorded on artifact for non-default arms.
        flags=a.get('policy',{});aa,ee=fit(replay,a['request'],**flags);check(aa==a and ee==e,'replay mismatch');replay['events'].append(e)
    return {'events':len(state['events']),'head':head,'catalog_count':len(rows),'active':active(rows),'dormant':sorted(set(rows)-set(active(rows))),'catalog':{G.pretty(bytes.fromhex(h)):v for h,v in rows.items()},'verified':True}

def pack(artifact):
    tx=artifact['request']['target']['inputs'];f=bytes.fromhex(artifact['frame']);decode(f,tx)
    context=zlib.compress(canonical(tx),9);return b'CP1'+L.u(len(context))+context+f

def unpack(blob):
    check(len(blob)<=131072,'package size');r=L.Reader(blob);check(r.take(3)==b'CP1','package magic');n=r.u();check(n<=65536,'context size');p=r.take(n);z=zlib.decompressobj();raw=z.decompress(p,65536);check(z.eof and not z.unused_data and not z.unconsumed_tail,'context compression');xs=json.loads(raw);f=r.take(len(r.b)-r.p);return {'inputs':xs,'outputs':decode(f,xs)}

def main():
    p=argparse.ArgumentParser(description=__doc__);sp=p.add_subparsers(dest='cmd',required=True)
    q=sp.add_parser('init');q.add_argument('state');q.add_argument('--cold',action='store_true')
    q=sp.add_parser('compile');q.add_argument('state');q.add_argument('request');q.add_argument('artifacts');q.add_argument('--legacy-search',action='store_true')
    q=sp.add_parser('verify');q.add_argument('state');q.add_argument('artifacts')
    q=sp.add_parser('decode');q.add_argument('artifact')
    q=sp.add_parser('inspect');q.add_argument('state')
    q=sp.add_parser('pack');q.add_argument('artifact');q.add_argument('package')
    q=sp.add_parser('unpack');q.add_argument('package')
    a=p.parse_args()
    if a.cmd=='init':check(not Path(a.state).exists(),'state exists');atomic(a.state,state_init(not a.cold));out={'initialized':a.state}
    elif a.cmd=='compile':obj,event=compile_file(a.state,load(a.request),a.artifacts,sufficiency=not a.legacy_search);out={'artifact':event['artifact'],'expression':obj['expression'],'admitted':obj['admitted'],'accounting':obj['accounting'],'stages':obj['stages'],'sufficiency':obj.get('sufficiency')}
    elif a.cmd=='verify':out=verify(a.state,a.artifacts)
    elif a.cmd=='decode':obj=load(a.artifact);out=decode(bytes.fromhex(obj['frame']),obj['request']['target']['inputs'])
    elif a.cmd=='pack':
        b=pack(load(a.artifact));Path(a.package).write_bytes(b);out={'package_bytes':len(b)}
    elif a.cmd=='unpack':out=unpack(Path(a.package).read_bytes())
    else:
        rows,head=entries(load(a.state));out={'head':head,'active':active(rows),'rows':rows}
    print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
