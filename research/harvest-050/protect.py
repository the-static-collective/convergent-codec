"""Create pinned XOR stripe equations from an explicitly selected complete capture."""
import argparse,json
from pathlib import Path
import harvest as h,circulation as c,commonwealth as cw,interdependence as id1,sensation as sn

def protect(manifest,mp,store,out,width=2):
    store,out=h.disjoint([store,out]);c.need(not out.exists() and out.parent.is_dir() and store.is_dir(),'fresh output and source store required');refs=sorted(c.validate(manifest));c.need(h.pin(manifest)==mp and 2<=width<=8 and len(refs)<=id1.MAX_VARS,'pin or stripe bounds');objects={}
    for k in refs:
        row,b=sn.probe(store,k);c.need(row['status']=='verified','complete source required');objects[k]=b
    records=[];parity={};covered=set()
    for i in range(0,len(refs),width):
        group=refs[i:i+width]
        if len(group)<2:continue
        r,b=id1.equation(objects,dict.fromkeys(group,1));records.append(r);parity[r['parity']]=b;covered.update(group)
    out.mkdir();(out/'objects').mkdir()
    for k,b in parity.items():cw.save_object(out/'objects',k,b)
    h.write(out/'equations.json',records);receipt=dict(manifest_pin=mp,record_pin=h.pin(records),equations=len(records),covered=len(covered),unprotected=sorted(set(refs)-covered));h.write(out/'protection.json',receipt);return receipt
if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('manifest');a.add_argument('pin');a.add_argument('store');a.add_argument('output');a.add_argument('--width',type=int,default=2);z=a.parse_args();print(json.dumps(protect(h.read(z.manifest),z.pin,z.store,z.output,z.width),indent=2))
