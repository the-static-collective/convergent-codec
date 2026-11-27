"""Posthoc exact three-atom union control, with no learned vocabulary."""
import itertools, json
from pathlib import Path
import circulation as c
from benchmark import fixture,KINDS

def encode(field,truth):
    wire,n=field.encode(truth,(),True)
    if len(wire)<=6:return wire,n
    eligible=[(i,a) for i,a in enumerate(field.atoms) if a and all(truth.get(k)==v for k,v in a.items())]
    for (i,a),(j,b),(k,d) in itertools.combinations(eligible,3):
        if a|b|d==truth:return bytes((4,i,j,k,0,0)),0
    return wire,n

def decode(field,wire):
    if wire and wire[0]==4:
        c.need(len(wire)==6 and wire[-2:]==b'\0\0' and wire[1]<wire[2]<wire[3]<len(field.atoms),'triple code')
        return field.atoms[wire[1]]|field.atoms[wire[2]]|field.atoms[wire[3]]
    return field.decode(wire,(),True)

if __name__=='__main__':
    out={}
    for name,start in [('heldout',3541),('fresh',3581),('new',3621)]:
        rows=[]
        for kind in KINDS:
            for seed in range(start,start+8):
                f,d=fixture(seed,kind);w,n=encode(f,d);assert decode(f,w)==d
                a,b=f.encode(d,['except-group'],True);assert f.decode(a,['except-group'],True)==d
                rows.append(dict(kind=kind,bytes=len(w),exact=n==0,learned_bytes=len(a),learned_exact=b==0))
        out[name]={'total':2+sum(r['bytes'] for r in rows),'exact':sum(r['exact'] for r in rows),'learned_total':16+sum(r['learned_bytes'] for r in rows),'learned_exact':sum(r['learned_exact'] for r in rows),'rows':rows}
        print(name,{k:v for k,v in out[name].items() if k!='rows'},flush=True)
    Path('triple.json').write_text(json.dumps(out,indent=2))
