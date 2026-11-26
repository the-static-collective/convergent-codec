"""RC1: plan-only voluntary gift allocation, with optional reciprocity scoring.
Units are abstract consumables. Gifts never create enforceable claims.
"""
from dataclasses import dataclass
POLICIES=('none','gift','direct','indirect','reserve','verified','verified-reserve')
@dataclass(frozen=True)
class Offer:
    stock:int
    floor:int
    cap:int
    recipients:tuple

def need(ok,msg):
    if not ok:raise ValueError(msg)

def allocate(offers,claims,evidence,history,policy='verified-reserve',buffer=2):
    n=len(offers);need(policy in POLICIES and 1<=n<=32 and len(claims)==len(evidence)==len(history)==n and all(len(row)==n for row in history),'field')
    need(type(buffer) is int and 0<=buffer<=100 and all(type(v) is int and 0<=v<=10000 for v in (*claims,*evidence,*(v for row in history for v in row))),'units')
    for o in offers:need(all(type(x) is int and 0<=x<=10000 for x in (o.stock,o.floor,o.cap)) and all(type(j) is int and 0<=j<n for j in o.recipients),'offer')
    if policy=='none':return ()
    limit=[min(c,e) if policy.startswith('verified') else c for c,e in zip(claims,evidence)]
    supply=[min(o.cap,max(0,o.stock-o.floor-(buffer if policy in ('reserve','verified-reserve') else 0))) for o in offers]
    received=[0]*n;sent=[0]*n;h=[list(row) for row in history];out=[]
    while True:
        choices=[]
        for i,o in enumerate(offers):
            if sent[i]>=supply[i]:continue
            for j in sorted(set(o.recipients)):
                if i==j or received[j]>=limit[j]:continue
                if policy=='direct' and h[i][j]-h[j][i]>=2:continue
                if policy=='indirect' and sum(h[k][j] for k in range(n))-sum(h[j])>=2:continue
                # Fair fraction served, then remaining claimed gap, then donor headroom.
                choices.append(((received[j]/limit[j],-(limit[j]-received[j]),-(supply[i]-sent[i]),j,i),i,j))
        if not choices:break
        _,i,j=min(choices);out.append((i,j));sent[i]+=1;received[j]+=1;h[i][j]+=1
    return tuple(out)

def verify(offers,claims,actions):
    """Independent replay of per-call consent and resource constraints."""
    n=len(offers);need(len(claims)==n,'claim count');sent=[0]*n;received=[0]*n
    for i,j in actions:
        need(type(i) is int and type(j) is int and 0<=i<n and 0<=j<n and i!=j and j in offers[i].recipients,'consent')
        sent[i]+=1;received[j]+=1;need(sent[i]<=min(offers[i].cap,max(0,offers[i].stock-offers[i].floor)) and received[j]<=claims[j],'quota or claim')
    return tuple(sent),tuple(received)
