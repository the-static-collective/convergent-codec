import hashlib, os, random, struct, unittest, zlib
from convergent_embodiment import codec as c

class CodecTests(unittest.TestCase):
    def check(self, blocks):
        frame, w = c.encode(blocks)
        self.assertEqual(c.decode(frame), blocks)
        self.assertEqual(frame,c.encode(blocks)[0])
        self.assertEqual(len(frame),c.HEADER.size+sum(x['emitted_bytes'] for x in w))
        self.assertLessEqual(len(frame),len(c.encode(blocks,structural=False)[0]))
        for row in w:self.assertEqual(row['emitted_bytes'],row['candidate_bytes'][str(row['mode'])])
        return frame
    def test_empty(self):self.check([]);self.check([b''])
    def test_binary(self):self.check([bytes(range(256))*100,os.urandom(c.BLOCK)])
    def test_source(self):self.check([b'def foo(x):\n    return x+x\n', 'def f(é):\n    return é\n'.encode()])
    def test_random(self):
        r=random.Random(2201)
        for _ in range(40):self.check([r.randbytes(r.randrange(1000)) for _ in range(r.randrange(1,8))])
    def test_modes(self):
        s=b'def long_name(argument):\n'+b'    argument = argument + 1\n'*40+b'    return argument\n'
        n=c.normalize(s);self.assertIsNotNone(n)
        for tag,p,rh,nh in [(0,s,b'',b''),(1,c.deflate(s),b'',b''),(2,c.deflate(s,s),s,b''),(3,c.deflate(n),b'',b''),(4,c.deflate(n,n),b'',n)]:
            self.assertEqual(c.decode_record(tag,p,len(s),rh,nh),s)
    def test_truncation(self):
        f=self.check([b'abc'*100,b'def f(x):\n return x\n'])
        for i in range(len(f)):
            with self.assertRaises(c.FormatError):c.decode(f[:i])
    def test_corruption(self):
        f=self.check([b'abc'*100,b'xyz'*100]);
        for i in (0,4,8,9,13,17,len(f)-1):
            q=bytearray(f);q[i]^=255
            with self.assertRaises(c.FormatError):c.decode(bytes(q))
        with self.assertRaises(c.FormatError):c.decode(f+b'!')
    def test_limits(self):
        for x in [c.HEADER.pack(c.MAGIC,c.MAX_BLOCKS+1),c.HEADER.pack(c.MAGIC,1)+c.RECORD.pack(1,c.BLOCK+1,0,b'0'*32),c.HEADER.pack(c.MAGIC,1)+c.RECORD.pack(1,0,c.BLOCK+1,b'0'*32)]:
            with self.assertRaises(c.FormatError):c.decode(x)
        with self.assertRaises(c.FormatError):c.encode([b'x'*(c.BLOCK+1)])
    def test_bomb(self):
        p=zlib.compress(b'A'*1000000)
        for tag in (1,3):
            f=c.HEADER.pack(c.MAGIC,1)+c.RECORD.pack(tag,1,len(p),b'0'*32)+p
            with self.assertRaises(c.FormatError):c.decode(f)
    def test_invalid_normalization(self):
        for rep in (b'',c.pack([b'\0',b'']),c.pack([b'\0\x01\x00',c.pack([b'x'])]),c.pack([b'\0\x00\x00'*100,c.pack([b'x'*100])])):
            with self.assertRaises(c.FormatError):c.restore(rep,10)
    def test_invalid_stream(self):
        for x in [zlib.compress(b'x')+b'x',zlib.compress(b'x')+zlib.compress(b'y'),zlib.compress(b'x')[:-1]]:
            with self.assertRaises(c.FormatError):c.inflate(x,10)
    def test_missing_history(self):
        for tag in (2,4,255):
            with self.assertRaises(c.FormatError):c.decode_record(tag,b'',0,b'',b'')
    def test_random_malformed(self):
        r=random.Random(2222)
        for _ in range(1000):
            b=r.randbytes(r.randrange(100))
            with self.assertRaises(c.FormatError):c.decode(b)
    def test_structured_mutation(self):
        r=random.Random(2202);f=self.check([b'alpha beta gamma '*100,b'alpha beta delta '*100])
        for _ in range(500):
            b=bytearray(f);i=r.randrange(len(b));b[i]^=r.randrange(1,256)
            try: x=c.decode(bytes(b))
            except c.FormatError: continue
            self.assertEqual(x,[b'alpha beta gamma '*100,b'alpha beta delta '*100])
if __name__=='__main__': unittest.main()
