"""EC1: bounded, dependency-free experimental byte-stream codec."""
import hashlib, io, keyword, struct, tokenize, zlib

MAGIC = b'EC1\0'
BLOCK = 65536
MAX_BLOCKS = 1024
MAX_TOTAL = BLOCK * MAX_BLOCKS
MAX_FRAME = MAX_TOTAL + MAX_BLOCKS * 80 + 64
MAX_REP = BLOCK * 4
WINDOW = 32768
U = struct.Struct('<I')
HEADER = struct.Struct('<4sI')
RECORD = struct.Struct('<BII32s')

class FormatError(ValueError):
    pass

def require(condition, message):
    if not condition:
        raise FormatError(message)

def pack(parts):
    return b''.join(U.pack(len(p)) + p for p in parts)

def unpack(data, limit=65536):
    out, i = [], 0
    while i < len(data):
        require(len(out) < limit and i + 4 <= len(data), 'invalid vector')
        n = U.unpack_from(data, i)[0]; i += 4
        require(n <= len(data)-i, 'truncated vector')
        out.append(data[i:i+n]); i += n
    return out

def restore(rep, cap=BLOCK):
    parts = unpack(rep, 2)
    require(len(parts) == 2, 'invalid normalized representation')
    skeleton, table = parts; names = unpack(table)
    out = bytearray(); i = 0
    while i < len(skeleton):
        j = skeleton.find(b'\0', i)
        if j < 0:
            require(len(out)+len(skeleton)-i <= cap, 'expanded block too large')
            out.extend(skeleton[i:]); break
        require(j+3 <= len(skeleton), 'truncated identifier')
        idx = int.from_bytes(skeleton[j+1:j+3], 'little')
        require(idx < len(names), 'invalid identifier')
        name = names[idx]
        require(len(out)+j-i+len(name) <= cap, 'expanded block too large')
        out.extend(skeleton[i:j]); out.extend(name); i = j+3
    return bytes(out)

def normalize(data):
    if b'\0' in data: return None
    try:
        s = data.decode('utf-8'); offsets = [0]
        for line in s.splitlines(keepends=True): offsets.append(offsets[-1]+len(line))
        names, pieces, last = {}, [], 0
        for t in tokenize.generate_tokens(io.StringIO(s).readline):
            if t.type != tokenize.NAME or keyword.iskeyword(t.string): continue
            a = offsets[t.start[0]-1]+t.start[1]; b = offsets[t.end[0]-1]+t.end[1]
            idx = names.setdefault(t.string, len(names))
            pieces.extend((s[last:a].encode(), b'\0'+idx.to_bytes(2,'little'))); last = b
        pieces.append(s[last:].encode())
        rep = pack([b''.join(pieces), pack([n.encode() for n in names])])
        if len(rep) <= MAX_REP and restore(rep, len(data)) == data: return rep
    except (UnicodeError, ValueError, OverflowError, IndexError, SyntaxError, tokenize.TokenError):
        pass
    return None

def deflate(data, dictionary=b''):
    if not dictionary: return zlib.compress(data, 9)
    c = zlib.compressobj(9, zdict=dictionary)
    return c.compress(data)+c.flush()

def inflate(data, cap, dictionary=b''):
    try:
        d = zlib.decompressobj(zdict=dictionary) if dictionary else zlib.decompressobj()
        out = d.decompress(data, cap+1)
        require(len(out)<=cap and d.eof and not d.unused_data and not d.unconsumed_tail, 'invalid or oversized DEFLATE')
        return out
    except zlib.error as e:
        raise FormatError('invalid DEFLATE') from e

def decode_record(tag, payload, size, raw_history, norm_history):
    if tag == 0: out = payload
    elif tag == 1: out = inflate(payload, size)
    elif tag == 2:
        require(bool(raw_history), 'missing raw history'); out = inflate(payload, size, raw_history)
    elif tag in (3,4):
        require(tag == 3 or bool(norm_history), 'missing normalized history')
        out = restore(inflate(payload, MAX_REP, norm_history if tag == 4 else b''), size)
    else: raise FormatError('unknown record mode')
    require(len(out)==size, 'block length mismatch')
    return out

def _encode(blocks, *, structural=True, rolling=True, seed=False):
    require(len(blocks)<=MAX_BLOCKS, 'too many blocks')
    parts=[HEADER.pack(MAGIC,len(blocks))]; raw_history=norm_history=b''; witness=[]
    for x in blocks:
        require(isinstance(x,bytes) and len(x)<=BLOCK, 'invalid block')
        n=normalize(x) if structural else None
        choices=[(0,x),(1,deflate(x))]
        if rolling and raw_history: choices.append((2,deflate(x,raw_history)))
        if n is not None:
            choices.append((3,deflate(n)))
            if rolling and norm_history: choices.append((4,deflate(n,norm_history)))
        for tag,p in choices:
            require(decode_record(tag,p,len(x),raw_history,norm_history)==x,'candidate mismatch')
        tag,p=min(choices,key=lambda q:(len(q[1]),q[0],q[1]))
        if seed and rolling and not norm_history and n is not None:
            q=next(q for q in choices if q[0]==3)
            if len(q[1])<=len(x): tag,p=q
        parts.extend((RECORD.pack(tag,len(x),len(p),hashlib.sha256(x).digest()),p))
        witness.append({'mode':tag,'source_bytes':len(x),'emitted_bytes':RECORD.size+len(p),'candidate_bytes':{str(t):RECORD.size+len(v) for t,v in choices}})
        raw_history=(raw_history+x)[-WINDOW:]
        # Only normalized records update normalized history. This removes decoder tokenization and version coupling.
        if tag in (3,4): norm_history=(norm_history+n)[-WINDOW:]
    frame=b''.join(parts); require(len(frame)<=MAX_FRAME,'frame too large')
    return frame,witness

def encode(blocks, *, structural=True, rolling=True):
    # Compare entire serialized streams, including any speculative seed cost.
    baseline=_encode(blocks,structural=False,rolling=rolling)
    if not structural:return baseline
    candidates=[baseline,_encode(blocks,structural=True,rolling=rolling)]
    if rolling:candidates.append(_encode(blocks,structural=True,rolling=True,seed=True))
    return min(candidates,key=lambda q:(len(q[0]),q[0]))

def decode(frame):
    require(HEADER.size<=len(frame)<=MAX_FRAME,'invalid frame size')
    magic,count=HEADER.unpack_from(frame); require(magic==MAGIC and count<=MAX_BLOCKS,'invalid header')
    out=[]; i=HEADER.size; raw_history=norm_history=b''
    for _ in range(count):
        require(i+RECORD.size<=len(frame),'truncated record')
        tag,size,n,digest=RECORD.unpack_from(frame,i); i+=RECORD.size
        require(size<=BLOCK and n<=BLOCK and n<=len(frame)-i,'invalid record bounds')
        payload=frame[i:i+n]; i+=n
        x=decode_record(tag,payload,size,raw_history,norm_history)
        require(hashlib.sha256(x).digest()==digest,'digest mismatch')
        out.append(x); raw_history=(raw_history+x)[-WINDOW:]
        if tag in (3,4):
            rep=inflate(payload,MAX_REP,norm_history if tag==4 else b'')
            norm_history=(norm_history+rep)[-WINDOW:]
    require(i==len(frame),'trailing bytes')
    return out
