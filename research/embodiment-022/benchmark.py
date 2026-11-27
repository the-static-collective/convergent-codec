"""Reproducible EC1 benchmark; no external libraries or history."""
import hashlib,json,random,sysconfig,time,zlib,lzma,bz2
from pathlib import Path
from convergent_embodiment import codec as c

def main():
    r=random.Random(2226); names=lambda:'v_'+''.join(r.choices('abcdefghijklmnopqrstuvwxyz',k=14))
    renamed=[]
    for i in range(80):
        a,b,d=names(),names(),names()
        renamed.append((f'def {a}({b}):\n    {d} = {b}\n'+''.join(f'    {d} = ({d} + {j}) % 127\n' for j in range(24)) + f'    return {d}\n').encode())
    root=Path(sysconfig.get_path('stdlib')); actual=[]
    for n in ('pathlib.py','functools.py','collections/__init__.py','json/decoder.py','ast.py','textwrap.py'):
        p=root/n
        if p.is_file():
            x=p.read_bytes();actual.extend(x[i:i+c.BLOCK] for i in range(0,len(x),c.BLOCK))
    binary=[r.randbytes(2048) for _ in range(40)]
    workloads={'renamed':renamed,'real_stdlib':actual,'random_binary':binary,'mixed':[x for pair in zip(renamed[:40],binary) for x in pair]}
    out={}
    for name,blocks in workloads.items():
        row={'documents':len(blocks),'source_bytes':sum(map(len,blocks)),'input_sha256':hashlib.sha256(c.pack(blocks)).hexdigest()}
        for mode,opts in [('rolling',{'structural':False}),('ec1',{})]:
            t=time.perf_counter();f,w=c.encode(blocks,**opts);enc=time.perf_counter()-t;t=time.perf_counter();assert c.decode(f)==blocks;dec=time.perf_counter()-t
            row[mode]={'bytes':len(f),'encode_seconds':enc,'decode_seconds':dec,'modes':{str(k):sum(x['mode']==k for x in w) for k in range(5)}}
        raw=c.pack(blocks);row['offline']={}
        for key,enc,dec in [('zlib',lambda x:zlib.compress(x,9),zlib.decompress),('lzma',lzma.compress,lzma.decompress),('bz2',bz2.compress,bz2.decompress)]:
            q=enc(raw);assert dec(q)==raw;row['offline'][key]=len(q)
        out[name]=row
    print(json.dumps({'python':__import__('sys').version,'zlib':zlib.ZLIB_RUNTIME_VERSION,'workloads':out},indent=2))
if __name__=='__main__':main()
