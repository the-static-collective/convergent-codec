import copy
import unittest
import compiler as C
import sensory
import sufficiency as S


class SufficiencyTests(unittest.TestCase):
    def test_collision_certificate(self):
        bank={'inputs':[[1],[1],[2]],'outputs':[3,4,5]}
        self.assertEqual(S.collisions(bank),[{'input':[1],'outputs':[3,4],'indices':[0,1],'count':2}])

    def test_equal_repetitions_not_conflicts(self):
        bank={'inputs':[[1],[1]],'outputs':[3,3]}
        self.assertEqual(S.collisions(bank),[])

    def test_hold_exact_fallback(self):
        banks,_=sensory.graph_banks()
        req=sensory.graph_request(banks,2,'descendants')
        a,e=C.fit(C.state_init(),req,sufficiency=True)
        self.assertEqual(a['sufficiency']['resolution'],'OBSERVATION_COLLISION')
        self.assertEqual(a['stages'],[])
        self.assertIsNone(a['admitted'])
        self.assertEqual(C.unpack(C.pack(a)),req['target'])

    def test_target_independence(self):
        banks,_=sensory.graph_banks();req=sensory.graph_request(banks,2,'descendants')
        a,_=C.fit(C.state_init(),req,sufficiency=True)
        r=copy.deepcopy(req);r['target']['outputs']=[x+1 for x in r['target']['outputs']]
        b,_=C.fit(C.state_init(),r,sufficiency=True)
        self.assertEqual(a['sufficiency'],b['sufficiency'])
        self.assertEqual(a['selected'],b['selected'])

    def test_no_collision_not_proof(self):
        bank={'inputs':[[1]],'outputs':[3]}
        self.assertEqual(S.assess(bank,bank)['status'],'NO_COLLISION_OBSERVED')

if __name__=='__main__':unittest.main()
