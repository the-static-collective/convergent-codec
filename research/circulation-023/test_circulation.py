import unittest,tempfile,random,struct,zlib,json
from pathlib import Path
import circulation as c
class Tests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory(); self.r=Path(self.t.name); self.src=self.r/'src';self.src.mkdir();self.store=self.r/'store'
 def tearDown(self):self.t.cleanup()
 def sample(self):
  (self.src/'a').write_bytes(b'abc'*9000);(self.src/'empty').mkdir();(self.src/'zero').touch();(self.src/'copy').write_bytes(b'abc'*9000)
  return c.snapshot(self.src)
 def test_full_delta(self):
  m,o=self.sample();f=c.make_bundle(m,o);r=c.receive(f,self.store,self.r/'one');self.assertEqual(c.snapshot(self.r/'one')[0],m)
  self.assertLess(r['received_objects'],sum(len(x['chunks']) for x in m['files']))
  (self.src/'a').rename(self.src/'renamed');(self.src/'copy').unlink();m,o=c.snapshot(self.src);f=c.make_bundle(m,o,c.inventory(self.store));self.assertEqual(len(c.parse_bundle(f)[1]),0)
  c.receive(f,self.store,self.r/'two');self.assertEqual(c.snapshot(self.r/'two')[0],m);self.assertTrue((self.r/'one'/'copy').exists())
 def test_missing(self):
  m,o=self.sample();f=c.make_bundle(m,o,o)
  with self.assertRaises(c.Error):c.receive(f,self.store,self.r/'one')
  self.assertFalse((self.r/'one').exists())
 def test_corruption_repair(self):
  m,o=self.sample();c.receive(c.make_bundle(m,o),self.store,self.r/'one');h=next(iter(o));(self.store/h).write_bytes(b'bad')
  self.assertNotIn(h,c.inventory(self.store));f=c.make_bundle(m,o,c.inventory(self.store));c.receive(f,self.store,self.r/'two');self.assertEqual(c.snapshot(self.r/'two')[0],m)
 def test_bad_paths(self):
  for p in ('../x','/x','a/../../x','a\\b','C:x','CON','a.','a//b','a\x00b'):
   with self.assertRaises(c.Error):c.validate({'version':1,'dirs':[p],'files':[]})
  for dirs in (['a','A'],['a/b'],['a','a']):
   with self.assertRaises(c.Error):c.validate({'version':1,'dirs':dirs,'files':[]})
 def test_symlink(self):
  (self.src/'a').symlink_to('/etc/passwd')
  with self.assertRaises(c.Error):c.snapshot(self.src)
 def test_nonoverwrite(self):
  m,o=self.sample();self.assertRaises(c.Error,c.receive,c.make_bundle(m,o),self.store,self.src)
 def test_truncation(self):
  m,o=self.sample();f=c.make_bundle(m,o)
  for i in range(len(f)):
   with self.assertRaises(c.Error):c.parse_bundle(f[:i])
  with self.assertRaises(c.Error):c.parse_bundle(f+b'!')
 def test_random_mutations(self):
  m,o=self.sample();f=c.make_bundle(m,o);r=random.Random(23)
  for i in range(200):
   x=bytearray(f);x[r.randrange(len(x))]^=r.randrange(1,256)
   try:a,b=c.parse_bundle(bytes(x))
   except (c.Error,UnicodeError):continue
   # A changed but valid manifest is not authenticated; every delivered object is verified.
   self.assertTrue(all(c.digest(v)==h for h,v in b.items()))
 def test_bomb(self):
  p=zlib.compress(b'x'*(c.MAX_MANIFEST+1));f=c.H.pack(c.MAGIC,len(p),0)+p
  with self.assertRaises(c.Error):c.parse_bundle(f)
 def test_inventory(self):
  m,o=self.sample();b=c.inventory_wire(o);self.assertEqual(c.parse_inventory(b),sorted(o));self.assertRaises(c.Error,c.parse_inventory,b+b'x')
 def test_ec1(self):
  m,o=self.sample();f=c.make_bundle(m,o,engine='ec1');c.receive(f,self.store,self.r/'one');self.assertEqual(c.snapshot(self.r/'one')[0],m)
 def test_empty(self):
  m,o=c.snapshot(self.src);c.receive(c.make_bundle(m,o),self.store,self.r/'one');self.assertEqual(c.snapshot(self.r/'one')[0],m)
if __name__=='__main__':unittest.main()
