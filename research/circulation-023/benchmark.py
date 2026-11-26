import io,tarfile,lzma,zlib,time,random,tempfile,sysconfig,json,shutil
from pathlib import Path
import circulation as c

def tar(root):
 b=io.BytesIO()
 with tarfile.open(fileobj=b,mode='w',format=tarfile.USTAR_FORMAT) as t:
  for p in sorted(root.rglob('*')):
   a=t.gettarinfo(str(p),p.relative_to(root).as_posix());a.mtime=0;a.uid=a.gid=0;a.uname=a.gname='';a.mode=0o755 if p.is_dir() else 0o644
   if p.is_file():
    with p.open('rb') as f:t.addfile(a,f)
   else:t.addfile(a)
 return b.getvalue()
def run():
 with tempfile.TemporaryDirectory() as tmp:
  r=Path(tmp); src=r/'source';src.mkdir();stdlib=Path(sysconfig.get_path('stdlib'));names=['ast.py','textwrap.py','functools.py','json/decoder.py','collections/__init__.py','email/message.py','argparse.py','difflib.py']
  for n in names:
   p=src/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((stdlib/n).read_bytes())
  local=src/'codec';local.mkdir();
  for n in ('ec1.py','circulation.py','test_circulation.py'):(local/n).write_bytes((Path(__file__).parent/n).read_bytes())
  (src/'empty').mkdir();(src/'zero').touch();rng=random.Random(2301);(src/'binary.dat').write_bytes(rng.randbytes(256*1024));(src/'duplicate.py').write_bytes((src/'ast.py').read_bytes())
  states=[]; stores={k:r/k for k in ('fixed','cdc','cdc_ec1')}; stages=['initial','unchanged','rename_delete','prefix_insert','small_edits','new_file']
  for i,stage in enumerate(stages):
   if stage=='rename_delete':(src/'ast.py').rename(src/'renamed_ast.py');(src/'duplicate.py').unlink()
   if stage=='prefix_insert':
    p=src/'binary.dat';p.write_bytes(rng.randbytes(17)+p.read_bytes());p=src/'renamed_ast.py';p.write_bytes(b'# inserted header\n'+p.read_bytes())
   if stage=='small_edits':
    p=src/'binary.dat';b=bytearray(p.read_bytes());b[100000:100016]=rng.randbytes(16);p.write_bytes(b);p=src/'argparse.py';b=p.read_bytes();p.write_bytes(b.replace(b'ArgumentParser',b'ArgumentParserUpdated',2))
   if stage=='new_file':(src/'new.py').write_bytes((src/'textwrap.py').read_bytes()+b'\n# updated copy\n')
   t=tar(src); row={'stage':stage,'source_bytes':sum(p.stat().st_size for p in src.rglob('*') if p.is_file()),'tar_deflate':len(zlib.compress(t,9)),'tar_lzma':len(lzma.compress(t)),'modes':{}}
   for name,store in stores.items():
    mode='fixed' if name=='fixed' else 'cdc';engine='ec1' if name=='cdc_ec1' else 'deflate';start=time.perf_counter();m,o=c.snapshot(src,mode);known=c.inventory(store);inv=c.inventory_wire(known);wire=c.make_bundle(m,o,known,engine);enc=time.perf_counter()-start
    start=time.perf_counter();dest=r/f'{name}-{i}';receipt=c.receive(wire,store,dest);dec=time.perf_counter()-start
    if c.snapshot(dest,mode)[0]!=m:raise RuntimeError('roundtrip mismatch')
    row['modes'][name]={'bundle_bytes':len(wire),'inventory_bytes':len(inv),'total_wire_bytes':len(wire)+len(inv),'fresh_bundle_bytes':len(c.make_bundle(m,o,engine=engine)), 'store_payload_bytes':sum(p.stat().st_size for p in store.iterdir()),'encode_s':enc,'receive_s':dec,**receipt}
   states.append(row)
  return {'python':__import__('sys').version,'stages':states,'source':'eight actual Python stdlib modules, local EC1 and CC1 source/test files, synthetic random binary, controlled edits; not a Git clone'}
if __name__=='__main__':print(json.dumps(run(),indent=2))
