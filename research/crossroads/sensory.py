"""Crossroads 011: bounded real-source probe. No remote code execution."""
import ast, datetime as dt, json, statistics, sys, hashlib
from pathlib import Path
import compiler as C
P=Path(__file__).resolve().parent
S=P/'sources'
PARTS=('train','validate','target')

def graph_banks():
    seen=set(); banks=[]; stats=[]
    for name in ('codec','ledger','motif'):
        raw=(S/(name+'.py')).read_text(); tree=ast.parse(raw); out=[]; eligible=0; overlap=0
        for i,n in enumerate(ast.walk(tree)):
            children=list(ast.iter_child_nodes(n)); x=tuple(len(list(ast.iter_child_nodes(c))) for c in children)
            if not 1<=len(x)<=8 or max(x)>32:continue
            eligible+=1
            if x in seen:overlap+=1;continue
            grandchildren=sum(1 for c in children for _ in ast.iter_child_nodes(c))
            descendants=sum(1 for _ in ast.walk(n))-1
            out.append((x,grandchildren,descendants,i))
        # Keep repeated inputs within each partition; preserve conflicting labels, exclude only earlier partitions.
        seen.update(r[0] for r in out);banks.append(out)
        stats.append({'source':name,'ast_nodes':sum(1 for _ in ast.walk(tree)),'eligible':eligible,'excluded_overlap':overlap,'kept':len(out),'unique_contexts':len({r[0] for r in out}),'sha256':hashlib.sha256(raw.encode()).hexdigest()})
    return banks,stats

def graph_request(banks,field,name):
    return {'name':name,'source':'Commit-pinned public Python AST excerpts; see sources/PROVENANCE.txt',**{k:{'inputs':[list(r[0]) for r in b],'outputs':[r[field] for r in b]} for k,b in zip(PARTS,banks)}}

def timeline_request():
    rows=sorted((dt.datetime.fromisoformat(t.replace('Z','+00:00')),s) for t,s in (l.split() for l in (S/'jarvis_commits.tsv').read_text().splitlines()))
    gaps=[min(32,round((b[0]-a[0]).total_seconds()/1800)) for a,b in zip(rows,rows[1:])]
    seen=set();banks=[];stats=[]
    # split raw time intervals first; no shared underlying intervals across splits.
    for g in (gaps[:15],gaps[15:30],gaps[30:]):
        obs=[(tuple(g[i:i+3]),g[i+3]) for i in range(len(g)-3)]; kept=[r for r in obs if r[0] not in seen];seen.update(r[0] for r in kept);banks.append(kept);stats.append({'intervals':len(g),'possible':len(obs),'kept':len(kept),'excluded_overlap':len(obs)-len(kept)})
    r={'name':'JAR-VIS next observed commit gap','source':'45 public connector-returned commit timestamps, 2026-11-06 through 2026-11-26; half-hour units rounded and capped at 32; not a complete event stream',**{k:{'inputs':[list(x) for x,y in b],'outputs':[y for x,y in b]} for k,b in zip(PARTS,banks)}}
    return r,stats

def baselines(r):
    x=r['target']['inputs'];y=r['target']['outputs'];train=r['train']['outputs']; med=round(statistics.median(train)); preds={'train_median':[med]*len(y),'last_input':[v[-1] for v in x],'sum':[sum(v) for v in x]}
    return {k:{'exact':sum(a==b for a,b in zip(p,y)),'mae':sum(abs(a-b) for a,b in zip(p,y))/len(y)} for k,p in preds.items()}

def main():
    banks,graph_stats=graph_banks();timeline,time_stats=timeline_request();reqs=[graph_request(banks,1,'AST grandchildren (known graph identity control)'),graph_request(banks,2,'AST full descendants from child degrees (unknown structure)'),timeline]
    output=P/'evidence';output.mkdir(exist_ok=True); results={}
    for mode,learn,escalate in [('persistent',True,True),('frozen',False,False),('cold',True,True)]:
        d=output/mode;d.mkdir(exist_ok=True);state=d/'state.json';C.atomic(state,C.state_init(mode!='cold'));arts=d/'artifacts';res=[]
        for i,r in enumerate(reqs):
            C.atomic(d/f'request-{i}.json',r);a,e=C.compile_file(state,r,arts,allow_learning=learn,escalate=escalate)
            assert C.unpack(C.pack(a))==r['target'];p=d/f'frame-{i}.cp1';p.write_bytes(C.pack(a))
            baseline=dict(a,frame=a['baseline_frame']); t=r['target']; pred=[C.G.evaluate(bytes.fromhex(a['selected']),x) for x in t['inputs']] if a['selected'] else []
            res.append({'name':r['name'],'n':{k:len(r[k]['outputs']) for k in PARTS},'selected':a['expression'],'validation_exact':a['validation_exact'],'train_exact':a['train_exact'],'admitted':a['admitted'],'mode':a['mode'],'accepted_prediction_exact':a['prediction_exact'],'exploratory_unvalidated_exact':sum(v==w for v,w in zip(pred,t['outputs'])),'baselines':baselines(r),'accounting':a['accounting'],'pack_bytes':len(C.pack(a)),'literal_pack_bytes':len(C.pack(baseline)),'evaluations':sum(s['evaluations'] for s in a['stages']),'artifact':e['artifact']})
        results[mode]={'rows':res,'replay':C.verify(state,arts),'state_bytes':state.stat().st_size}
    C.atomic(output/'results.json',{'graph':graph_stats,'timeline':time_stats,'runs':results,'python':sys.version})
    print(json.dumps({'graph':graph_stats,'timeline':time_stats,'runs':{k:v['rows'] for k,v in results.items()}},indent=2))
if __name__=='__main__':main()
