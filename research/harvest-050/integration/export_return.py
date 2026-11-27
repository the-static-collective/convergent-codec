"""Export a private, non-authoritative recovery return card after a fresh readback."""
import argparse,json
from pathlib import Path
import harvest as h, circulation as c
SOURCE='8880092d729e8f9f01ad5bd34b1d2e158fc109fb'

def export(manifest,mp,receipt,rp,dest):
    m=h.read(manifest);c.need(h.pin(m)==mp,'manifest pin');refs=c.validate(m)
    raw=c.read_limited(Path(receipt),65536);c.need(c.digest(raw)==rp,'receipt bytes pin');r=json.loads(raw)
    c.need(set(r)=={'schema','plan_pin','manifest_pin','approval_ids','direct','regenerated','destination','verified_files'} and r['schema']=='HV1-restored' and r['manifest_pin']==mp,'receipt shape or manifest')
    c.need(c.valid_hash(r['plan_pin']) and isinstance(r['approval_ids'],list) and 1<=len(r['approval_ids'])<=33 and all(c.valid_hash(x) for x in r['approval_ids']) and len(set(r['approval_ids']))==len(r['approval_ids']),'receipt pins')
    c.need(all(type(r[k]) is int and 0<=r[k]<=c.MAX_OBJECTS for k in ('direct','regenerated','verified_files')) and r['direct']+r['regenerated']==len(refs) and r['verified_files']==len(m['files']),'receipt counts')
    dest=h.real(dest);c.need(str(dest)==r['destination'],'receipt destination mismatch');mm,_=c.snapshot(dest)
    def files(x):return [(f['path'],f['size'],f['sha256']) for f in x['files']]
    c.need(mm['dirs']==m['dirs'] and files(mm)==files(m),'readback differs')
    return dict(schema='harvest.return/v1',source_commit=SOURCE,manifest_pin=mp,receipt_sha256=rp,plan_pin=r['plan_pin'],verified_files=r['verified_files'],direct=r['direct'],regenerated=r['regenerated'],readback='matched',classification='PRIVATE_OPERATOR_HANDOFF',authority='NONE',admission='none')

def main():
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('manifest');a.add_argument('manifest_pin');a.add_argument('receipt');a.add_argument('receipt_sha256');a.add_argument('restored');a.add_argument('output');z=a.parse_args()
    card=export(z.manifest,z.manifest_pin,z.receipt,z.receipt_sha256,z.restored);h.write(z.output,card);print(json.dumps({'card_sha256':c.digest(Path(z.output).read_bytes()),'authority':'NONE','admission':'none'}))
if __name__=='__main__':main()
