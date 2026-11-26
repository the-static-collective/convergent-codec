"""Deterministic integration replay; targets are authored synthetic mechanisms."""
import compiler as C, genesis as G, json, pathlib, tempfile, statistics, hashlib, shutil, subprocess, sys
P=pathlib.Path(__file__).parent
TARGETS=[('energy mass first last',lambda x:x[-1]*x[0]*(sum(x)+sum(v*v for v in x))),('span mass plus first',lambda x:(max(x)-min(x))*sum(x)+x[0]),('weighted sum unknown',lambda x:sum((i+1)*v for i,v in enumerate(x))),('energy mass first last return',lambda x:x[-1]*x[0]*(sum(x)+sum(v*v for v in x))),('endpoint and peak times mass',lambda x:(max(x)+x[0]*x[-1])*sum(x)),('span mass plus first return',lambda x:(max(x)-min(x))*sum(x)+x[0])]
def request(i,name,fn):
    seen=set();r={'name':name,'source':'authored synthetic fixture; no external truth claim'}
    for j,k in enumerate(('train','validate','target')):
        xs=[]
        for x in G.bank(10100+i*100+j,256):
            if len(x)<=8 and tuple(x) not in seen:seen.add(tuple(x));xs.append(x)
            if len(xs)==(64 if k=='target' else 24):break
        r[k]={'inputs':xs,'outputs':[fn(x) for x in xs]}
    return r

def run(out,seed=True,learning=True,escalate=True):
    out.mkdir(parents=True,exist_ok=True);state=out/'state.json';arts=out/'artifacts';C.atomic(state,C.state_init(seed));summary=[]
    for i,(name,fn) in enumerate(TARGETS):
        r=request(i,name,fn);C.atomic(out/f'request-{i}.json',r);a,e=C.compile_file(state,r,arts,allow_learning=learning,escalate=escalate)
        summary.append({'name':name,'expression':a['expression'],'admitted':a['admitted'],'exact':a['prediction_exact'],'n':a['target_count'],'stages':a['stages'],'accounting':a['accounting']})
    v=C.verify(state,arts);return {'rows':summary,'totals':{k:sum(r['accounting'][k] for r in summary) for k in ['wire','baseline','saved','calibration_zlib_bytes','context_zlib_bytes']},'evaluations':sum(s['evaluations'] for r in summary for s in r['stages']),'complete':sum(r['exact']==r['n'] for r in summary),'admissions':sum(bool(r['admitted']) for r in summary),'verified':v['verified'],'catalog_count':v['catalog_count'],'state_bytes':state.stat().st_size,'artifact_bytes':sum(f.stat().st_size for f in arts.glob('*.json')),'catalog_frame_bytes':{k:len(f) for k,f in C.C.frames([bytes.fromhex(h) for h in C.entries(C.load(state))[0]]).items()}}

def main():
    base=P/'demo_output';base.mkdir(exist_ok=True)
    results={}
    for name,seed,learn,escalate in [('inherited',True,True,True),('no_learning',True,False,True),('cold',False,True,True),('frozen',True,False,False)]:
        results[name]=run(base/name,seed,learn,escalate);print(name,{k:v for k,v in results[name].items() if k!='rows'},flush=True)
    C.atomic(base/'results.json',results)
if __name__=='__main__':main()
