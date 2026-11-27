import tempfile,unittest
from pathlib import Path
import commonwealth as w
import circulation as c
class Test(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.r=Path(self.t.name);s=self.r/'src';s.mkdir();(s/'a').write_bytes(bytes(range(256))*300);(s/'b').write_bytes(b'hello');self.m,self.o=c.snapshot(s);self.pin=c.digest(c.canon(self.m));self.ps=[self.r/f'p{i}' for i in range(3)]
  for p in self.ps:p.mkdir()
  for i,(h,b) in enumerate(self.o.items()):w.save_object(self.ps[i%3],h,b)
 def tearDown(self):self.t.cleanup()
 def run_recover(self,**kw):return w.recover(self.m,self.pin,self.ps,self.r/'local',self.r/'out',**kw)
 def test_modes(self):
  for i,mode in enumerate(('blind','exact','bitmap')):
   r=w.recover(self.m,self.pin,self.ps,self.r/f'l{i}',self.r/f'o{i}',mode);self.assertTrue(r['restored']);self.assertEqual(c.snapshot(self.r/f'o{i}')[0],self.m)
 def test_pin(self):
  with self.assertRaises(c.Error):w.recover(self.m,'0'*64,self.ps,self.r/'local',self.r/'out')
 def test_missing_resume(self):
  r=self.run_recover(offline=(0,));self.assertFalse(r['restored']);self.assertFalse((self.r/'out').exists());r=self.run_recover();self.assertTrue(r['restored']);self.assertGreater(r['reused'],0)
 def test_corruption(self):
  h=next(iter(self.o));p=self.ps[0]/h;self.assertTrue(p.exists());ads=[c.inventory(x) for x in self.ps];p.write_bytes(b'broken');w.save_object(self.ps[2],h,self.o[h]);r=self.run_recover(advertised=ads);self.assertTrue(r['restored']);self.assertGreater(r['failed_requests'],0)
 def test_bitmap(self):
  refs=sorted(self.o);self.assertEqual(w.unbitmap(refs,w.bitmap(refs,refs[:1])),set(refs[:1]));self.assertRaises(c.Error,w.unbitmap,refs,b'')
 def test_replication(self):
  r=w.replicate(self.o,self.ps,100000,target=3);self.assertTrue(all(x==3 for x in r['counts'].values()));self.assertLessEqual(r['payload_bytes'],100000);self.assertTrue(self.run_recover(offline=(0,1))['restored'])
 def test_nonoverwrite(self):
  self.run_recover();self.assertRaises(c.Error,self.run_recover)
 def test_stale_false_negative(self):
  self.assertTrue(self.run_recover(advertised=[[],[],[]])['restored'])
if __name__=='__main__':unittest.main()
