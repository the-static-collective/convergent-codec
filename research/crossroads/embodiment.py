"""Crossroads 012: matched comparison and journal replay on 011's frozen inputs."""
import json
import tempfile
from pathlib import Path
import compiler as C
import sensory as T


def run():
    banks,_=T.graph_banks()
    reqs=[T.graph_request(banks,1,'grandchildren'),
          T.graph_request(banks,2,'descendants'),T.timeline_request()[0]]
    results=[]
    with tempfile.TemporaryDirectory() as d:
        state=Path(d)/'state'; arts=Path(d)/'arts'
        C.atomic(state,C.state_init())
        for r in reqs:
            # Isolated paired initial states, not sequential training across tasks.
            a,_=C.fit(C.state_init(),r)
            b,_=C.fit(C.state_init(),r,sufficiency=True)
            results.append({'name':r['name'],'status':b['sufficiency']['resolution'],
                'witness_counts':{k:len(v) for k,v in b['sufficiency']['witnesses'].items()},
                'example':next((v[0] for v in b['sufficiency']['witnesses'].values() if v),None),
                'old_evaluations':sum(x['evaluations'] for x in a['stages']),
                'new_evaluations':sum(x['evaluations'] for x in b['stages']),
                'old_bytes':a['accounting']['wire'],'new_bytes':b['accounting']['wire'],
                'exact':C.unpack(C.pack(b))==r['target']})
            C.compile_file(state,r,arts,sufficiency=True)
        replay=C.verify(state,arts)
    result={'results':results,'replay':replay['verified'],'events':replay['events']}
    assert all(row['exact'] for row in results)
    for mode in ['persistent','frozen','cold']:
        d=C.ROOT/'evidence'/mode
        assert C.verify(d/'state.json',d/'artifacts')['verified']
    return result

if __name__=='__main__':
    result=run()
    print(json.dumps(result,indent=2))
    C.atomic(C.ROOT/'embodiment_results.json',result)
