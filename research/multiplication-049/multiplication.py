"""MU1: tagged productive-resource lineage and bounded voluntary restoration planning."""
from collections import Counter
from restoration import Project,plan,check
from reciprocity import Offer,need
POLICIES=('relief','distributed','central','relief-first','guarded','growth')

class Stock:
    """Accounting convention: spend external units first, then oldest production tag."""
    def __init__(self,units=0):self.tags=Counter({-1:units})
    def total(self):return sum(self.tags.values())
    def add(self,origin,units):
        need(type(units) is int and units>=0,'units');self.tags[origin]+=units
    def take(self,n):
        need(type(n) is int and 0<=n<=self.total(),'stock');out=Counter()
        for k in sorted(self.tags):
            q=min(n,self.tags[k]);self.tags[k]-=q;n-=q
            if q:out[k]+=q
            if not n:break
        self.tags=+self.tags;return out

class Lineage:
    def __init__(self):self.nodes=[]
    def add(self,member,tick,funds):
        i=len(self.nodes);parents=tuple(sorted(k for k,v in funds.items() if k>=0 and v))
        need(all(k<i for k in parents),'parent must predate child')
        depth=1+max((self.nodes[k]['depth'] for k in parents),default=-1)
        self.nodes.append(dict(member=member,tick=tick,parents=parents,depth=depth,funds=dict(funds)))
        return i

def propose(offers,gaps,projects,accepted,recent,policy):
    need(policy in POLICIES,'policy')
    # Same RS1 planner and consent checks; topology selected by the caller.
    p={'relief':'relief','distributed':'hybrid','central':'hybrid','relief-first':'relief-first','guarded':'guarded','growth':'hybrid'}[policy]
    priority=[1]*len(gaps) if policy=='growth' else recent
    return plan(offers,gaps,projects,accepted,priority,p)
