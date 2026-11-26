import argparse, json, hashlib, os, tempfile
from pathlib import Path
from .codec import encode,decode,MAX_TOTAL,MAX_FRAME,BLOCK,FormatError

def read(p,cap):
    with open(p,'rb') as f: data=f.read(cap+1)
    if len(data)>cap: raise FormatError('input exceeds limit')
    return data

def atomic(path,data):
    p=Path(path); fd,name=tempfile.mkstemp(dir=p.parent)
    try:
        with os.fdopen(fd,'wb') as f: f.write(data)
        os.replace(name,p)
    finally:
        if os.path.exists(name): os.unlink(name)

def main():
    p=argparse.ArgumentParser(description='Experimental EC1 codec'); sub=p.add_subparsers(dest='command',required=True)
    for name in ('compress','decompress','inspect','benchmark'):
        q=sub.add_parser(name); q.add_argument('input')
        if name in ('compress','decompress'):q.add_argument('output')
        if name=='compress':q.add_argument('--witness')
    a=p.parse_args()
    try:
        if a.command in ('compress','benchmark'):
            x=read(a.input,MAX_TOTAL); blocks=[x[i:i+BLOCK] for i in range(0,len(x),BLOCK)]
            frame,w=encode(blocks)
            if b''.join(decode(frame))!=x:raise FormatError('final roundtrip failed')
            if a.command=='benchmark':
                base,_=encode(blocks,structural=False); print(json.dumps({'source_bytes':len(x),'rolling_baseline_bytes':len(base),'encoded_bytes':len(frame),'verified':True},indent=2));return
            paths=[Path(a.input).resolve(),Path(a.output).resolve()]+([Path(a.witness).resolve()] if a.witness else [])
            if len(set(paths))!=len(paths):raise FormatError('input, output and witness must be distinct')
            atomic(a.output,frame)
            if a.witness:atomic(a.witness,json.dumps({'format':'EC1','sha256':hashlib.sha256(frame).hexdigest(),'records':w},indent=2).encode())
        else:
            frame=read(a.input,MAX_FRAME); blocks=decode(frame); data=b''.join(blocks)
            if a.command=='inspect':print(json.dumps({'format':'EC1','records':len(blocks),'encoded_bytes':len(frame),'source_bytes':len(data),'verified':True,'source_sha256':hashlib.sha256(data).hexdigest()},indent=2))
            else:
                if Path(a.input).resolve()==Path(a.output).resolve():raise FormatError('input and output must differ')
                atomic(a.output,data)
    except (OSError,FormatError) as e:p.exit(2,f'EC1: {e}\n')
if __name__=='__main__':main()
