"""Bounded one-action minimax relative regret, four explicit copy-loss models."""
N=6
SINGLES=tuple(1<<p for p in range(N))
DOMAINS=tuple(3<<(2*p) for p in range(N//2))
RISK={m:tuple(sum(not (s & ~f) for f in m)/len(m) for s in range(1<<N)) for m in (SINGLES,DOMAINS)}
def mask(ps):return sum(1<<p for p in set(ps))
def benefits(active,ads,p,price):
    a,b=mask(active),mask(ads); bit=1<<p
    return tuple((RISK[m][s]-RISK[m][s|bit])/price for m,s in ((SINGLES,a),(SINGLES,b),(DOMAINS,a),(DOMAINS,b)))
def choose(candidates,objective="minimax"):
    """Each candidate: (deterministic tie key, h, p, price, recipe, benefits)."""
    if objective not in ("minimax","mean"):raise ValueError("unknown objective")
    if not candidates:return None
    maxima=[max(a[-1][i] for a in candidates) for i in range(4)]
    use=[i for i,m in enumerate(maxima) if m>0]
    if not use:return None
    def key(a):
        ratios=[a[-1][i]/maxima[i] for i in use]
        worst,mean=min(ratios),sum(ratios)/len(ratios)
        return (worst,mean,a[0]) if objective=="minimax" else (mean,worst,a[0])
    return max(candidates,key=key)[:-1]
