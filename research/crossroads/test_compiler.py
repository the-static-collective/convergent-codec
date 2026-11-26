import unittest,tempfile,copy,subprocess,sys,pathlib,json
import compiler as C, demo as D
class TestCompiler(unittest.TestCase):
    def setUp(self):
        self.state=C.state_init();self.request=D.request(0,*D.TARGETS[0]);self.a,self.e=C.fit(self.state,self.request)
    def test_roundtrip_pack(self):
        self.assertEqual(C.unpack(C.pack(self.a)),self.request['target'])
    def test_target_not_used_for_selection(self):
        r=copy.deepcopy(self.request);r['target']['outputs']=[v+1 for v in r['target']['outputs']];a,e=C.fit(self.state,r)
        for k in ['selected','admitted','train_exact','validation_exact','stages']:self.assertEqual(a[k],self.a[k])
    def test_digest(self):
        f=bytearray.fromhex(self.a['frame']);f[-1]^=1
        with self.assertRaises(ValueError):C.decode(bytes(f),self.request['target']['inputs'])
    def test_context(self):
        x=copy.deepcopy(self.request['target']['inputs']);x[0][0]+=1
        with self.assertRaises(ValueError):C.decode(bytes.fromhex(self.a['frame']),x)
    def test_chain(self):
        self.state['events'].append(self.e);C.entries(self.state);self.state['events'][0]['target_saved']+=1
        with self.assertRaises(ValueError):C.entries(self.state)
    def test_validation_gate(self):
        r=copy.deepcopy(self.request);r['validate']['outputs'][0]+=1;a,e=C.fit(self.state,r);self.assertIsNone(a['admitted']);self.assertFalse(a['validation_exact']);self.assertIn(a['mode'],'RZ')
    def test_reject_overlap(self):
        r=copy.deepcopy(self.request);r['validate']['inputs'][0]=r['train']['inputs'][0]
        with self.assertRaises(ValueError):C.fit(self.state,r)
    def test_cli_restart(self):
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d);state=p/'state';req=p/'request';arts=p/'arts';C.atomic(req,self.request)
            def cli(*a):return json.loads(subprocess.check_output([sys.executable,str(C.ROOT/'compiler.py'),*map(str,a)]))
            cli('init',state);r=cli('compile',state,req,arts);v=cli('verify',state,arts);self.assertEqual(v['events'],1);self.assertTrue(v['verified']);f=arts/(r['artifact']+'.json');cli('pack',f,p/'payload.cp1');self.assertEqual(cli('unpack',p/'payload.cp1'),self.request['target'])
            obj=C.load(f);obj['name']='tampered';C.atomic(f,obj)
            with self.assertRaises(ValueError):C.verify(state,arts)
if __name__=='__main__':unittest.main()
