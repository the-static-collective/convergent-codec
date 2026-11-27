"""RC1 signed batch receipts. Trusted current checkpoint, roster and stock external.
No persistent transaction or actual resource delivery. Advance checkpoint only once externally.
"""
from dataclasses import dataclass,asdict
import covenant as c
from reciprocity import Offer,verify
@dataclass(frozen=True)
class Checkpoint:
    round:int
    used:tuple
    head:str=c.ZERO
    limit:int=10

def frame(keys,checkpoint,offers,claims,evidence,observation=c.ZERO):
    limit=checkpoint.limit
    c.need(c.hexstr(observation,64),'observation pin')
    n=len(keys);c.need(1<=n<=32 and len(set(keys))==n and all(c.hexstr(k,64) for k in keys),'roster')
    c.need(c.integer(checkpoint.round,0,2**53-1) and c.hexstr(checkpoint.head,64) and len(checkpoint.used)==n and c.integer(limit,0,10000) and all(c.integer(u,0,limit) for u in checkpoint.used),'checkpoint')
    c.need(len(offers)==len(claims)==len(evidence)==n,'field size')
    # The checkpoint is the prior round's cumulative outflow; start a new window every eight rounds.
    used=(0,)*n if checkpoint.round%8==0 else checkpoint.used
    effective=[]
    for i,o in enumerate(offers):
        c.need(all(c.integer(x,0,10000) for x in (o.stock,o.floor,o.cap,claims[i],evidence[i])) and all(c.integer(j,0,n-1) for j in o.recipients),'field values')
        effective.append(Offer(o.stock,o.floor,min(o.cap,limit-used[i]),tuple(o.recipients)))
    body=dict(keys=list(keys),checkpoint=asdict(checkpoint),offers=[asdict(o) for o in offers],claims=list(claims),evidence=list(evidence),observation=observation)
    return c.digest(body),tuple(effective),used

def assent(key,frame_id,actions):
    return c.signed(key,dict(issuer=c.key(key),frame=frame_id,actions=[list(a) for a in actions]),'rc-batch')

def commit(keys,checkpoint,offers,claims,evidence,actions,signatures,observation=c.ZERO):
    fid,eff,used=frame(keys,checkpoint,offers,claims,evidence,observation)
    sent,received=verify(eff,claims,actions);required={keys[i] for a in actions for i in a};seen=set()
    c.need(isinstance(signatures,list) and len(signatures)==len(required),'assent count')
    for sig in signatures:
        b=c.check(sig,'rc-batch');c.shape(b,'issuer frame actions');c.need(b['issuer'] in required and b['issuer'] not in seen and b['frame']==fid and b['actions']==[list(a) for a in actions],'assent binding');seen.add(b['issuer'])
    receipt=dict(schema='RC1',frame=fid,actions=[list(a) for a in actions],sent=sent,received=received,prior=checkpoint.head,signatures=signatures)
    return Checkpoint(checkpoint.round+1,tuple(a+b for a,b in zip(used,sent)),c.digest(receipt),checkpoint.limit),receipt
