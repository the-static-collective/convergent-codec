import unittest,random
from anticipation import Anticipation,Rates,POLICIES
from analogy import apply
from benchmark import fixture,run
class Test(unittest.TestCase):
 def test_budget(self):
  for p in POLICIES:
   for b in (1,3,5,10):
    g=Anticipation(4,p,budget=b);x=(0,1,2,1);g.boot([(x,x)],'a')
    for t in range(50):
     if g.step(str(t%7),t%3==0):g.observe(x,x)
     if t%10==9:self.assertEqual(g.used,b)
 def test_causal_prefix(self):
  fx=fixture(41501,'warning')
  for p in POLICIES:
   a,full=run(fx,p,1,trace=True);b,prefix=run((fx[0],fx[1][:37]),p,1,trace=True);self.assertEqual(full[:37*3],prefix)
 def test_freshness(self):
  g=Anticipation(4);x=(0,1,2,1);g.boot([(x,x)],'a');self.assertTrue(g.step('a',False));g.observe(x,x);self.assertEqual(g.predict(x,0)[0],x);self.assertFalse(g.step('a',False));self.assertEqual(g.predict(x,0),(None,'stale-abstention'))
 def test_pending(self):
  g=Anticipation(4);x=(0,1,2,1);g.boot([(x,x)],'a');self.assertTrue(g.step('a',False));self.assertRaises(ValueError,g.step,'a',False);self.assertRaises(ValueError,g.predict,x);g.observe(x,x);self.assertRaises(ValueError,g.observe,x,x)
 def test_context_reset(self):
  g=Anticipation(4);x=(0,1,2,1);g.boot([(x,x)],'a');g.step('a',False);g.observe(x,x);self.assertFalse(g.step('b',False));self.assertIsNone(g.last);self.assertIsNone(g.predict(x,4)[0])
 def test_rates(self):
  r=Rates();self.assertEqual(r.rate(0,0),.5);r.add(0,0,True);r.add(0,0,False);self.assertEqual(r.rate(0,0),.5);r.add(1,7,True);self.assertAlmostEqual(r.rate(1,7),2/3)
 def test_fresh_not_truth(self):
  g=Anticipation(4);r=random.Random(2);a=(0,1,2,3);b=(1,0,2,3);boot=[(x,x) for x in [tuple(r.randrange(3) for _ in range(4)) for _ in range(10)]];g.boot(boot,'a');g.step('a',True);x=(0,0,1,2);g.observe(x,apply(x,b));q=(0,1,2,0);self.assertEqual(g.predict(q,0)[0],q);self.assertNotEqual(g.predict(q,0)[0],apply(q,b))
 def test_phase(self):
  x=(0,1,2,1)
  def slots(policy):
   g=Anticipation(4,policy);g.boot([(x,x)],'a');out=[]
   for t in range(10):
    if g.step('a',t in (0,3,6)):out.append(t);g.observe(x,x)
   return out
  self.assertEqual(slots('phase'),[1,4,7]);self.assertEqual(slots('paced'),[0,3,6])
if __name__=='__main__':unittest.main()
