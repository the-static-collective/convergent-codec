"""AC1: bounded grammar admission using exact residual coding of SN1 observations."""
import json,struct,itertools
import circulation as c
# Rule vocabulary is supplied, not autonomously invented. Ordered peer/group labels.
FAMILIES=('pair-peer','pair-group','except-peer','except-group','mixed-peer')
STATES=('verified','missing','corrupt'); STATUS=('missing','corrupt')

def grammar_bytes(families):
    c.need(len(set(families))==len(families) and set(families)<=set(FAMILIES),'invalid grammar')
    return c.canon(list(families))

class Field:
    def __init__(self,baseline,groups):
        from curiosity import catalog
        self.base,self.models=catalog(baseline,groups)
        self.pin=baseline['manifest_pin'];self.keys=sorted(self.base);self.peers=sorted(baseline['peers']);self.groups=sorted(set(groups.values()));self.tags=groups
        c.need(len(self.peers)==4 and len(self.groups)==4,'AC1 experimental four-peer four-group field')
        self.index={k:i for i,k in enumerate(self.keys)};self.atoms=[self.models[k] for k in sorted(self.models)]
        self.rows={}
        for p in range(4):
            for g in range(4):
                self.rows[p,g]={k for k in self.keys if k[0]==self.peers[p] and groups[k[1]]==self.groups[g] and self.base[k]=='verified'}
    def delta(self,report):
        c.need(report['schema']=='SN1' and report['manifest_pin']==self.pin and report.get('record_pin') is None and set(report['peers'])==set(self.peers),'report identity')
        out={}
        for p,row in report['peers'].items():
            c.need(row['root_status']=='accessible' and set(row['observations'])=={h for q,h in self.keys if q==p},'full accessible observation required')
            for h,v in row['observations'].items():
                x=v['status'];c.need(x in STATES,'decisive observation required')
                if x!=self.base[p,h]:out[p,h]=x
        return out
    def rule(self,f,p,g,k):
        c.need(f in FAMILIES and 0<=p<4 and 0<=g<4 and 0<=k<2,'rule parameter')
        v=STATUS[k];a=self.rows[p,g]
        if f=='pair-peer':b=self.rows[(p+1)%4,g]
        elif f=='pair-group':b=self.rows[p,(g+1)%4]
        elif f=='except-peer':a=set();b=set().union(*(self.rows[q,g] for q in range(4) if q!=p))
        elif f=='except-group':a=set();b=set().union(*(self.rows[p,j] for j in range(4) if j!=g))
        else:return {**dict.fromkeys(a,v),**dict.fromkeys(self.rows[(p+1)%4,g],STATUS[1-k])}
        return dict.fromkeys(a|b,v)
    def candidates(self,families,compose=False):
        yield bytes((0,)),{}
        for i,a in enumerate(self.atoms):yield bytes((1,i)),a
        if compose:
            for i,a in enumerate(self.atoms):
                for j,b in enumerate(self.atoms):
                    if i!=j:yield bytes((2,i,j)),a|b
        for i,f in enumerate(families):
            for p,g,k in itertools.product(range(4),range(4),range(2)):
                yield bytes((3,i,p*8+g*2+k)),self.rule(f,p,g,k)
    def residual(self,truth,pred):
        r=[]
        for key in sorted(truth.keys()|pred.keys()):
            a=truth.get(key,self.base[key]);b=pred.get(key,self.base[key])
            if a!=b:r.append((self.index[key],STATES.index(a)))
        return r
    def encode(self,truth,families=(),compose=False):
        grammar_bytes(families);best=None
        for head,pred in self.candidates(families,compose):
            r=self.residual(truth,pred);size=len(head)+2+3*len(r);score=(size,len(r),head)
            if best is None or score<best[0]:best=(score,head,r)
        _,head,r=best
        return head+struct.pack('<H',len(r))+b''.join(struct.pack('<HB',i,v) for i,v in r),len(r)
    def decode(self,wire,families=(),compose=False):
        grammar_bytes(families);c.need(len(wire)>=3,'short code');tag=wire[0];n=1
        if tag==0:pred={}
        elif tag==1:
            c.need(len(wire)>=4 and wire[1]<len(self.atoms),'atom');pred=self.atoms[wire[1]];n=2
        elif tag==2:
            c.need(compose and len(wire)>=5 and max(wire[1:3])<len(self.atoms),'composition');pred=self.atoms[wire[1]]|self.atoms[wire[2]];n=3
        elif tag==3:
            c.need(len(wire)>=5 and wire[1]<len(families) and wire[2]<32,'rule');p,g,k=wire[2]//8,wire[2]//2%4,wire[2]%2;pred=self.rule(families[wire[1]],p,g,k);n=3
        else:raise c.Error('unknown code')
        count=struct.unpack_from('<H',wire,n)[0];n+=2;c.need(len(wire)==n+3*count,'residual length');out=dict(pred);last=-1
        for i,v in struct.iter_unpack('<HB',wire[n:]):
            c.need(last<i<len(self.keys) and v<len(STATES),'invalid residual');last=i;key=self.keys[i];x=STATES[v]
            if x==self.base[key]:out.pop(key,None)
            else:out[key]=x
        return out

def train(examples,compose=False):
    """Greedy dictionary selection by total paid bytes on training only."""
    def cost(fs):return len(grammar_bytes(fs))+sum(len(field.encode(delta,fs,compose)[0]) for field,delta in examples)
    chosen=[];current=cost(chosen);history=[]
    while True:
        options=[(cost(chosen+[f]),f) for f in FAMILIES if f not in chosen]
        if not options:break
        n,f=min(options)
        if n>=current:break
        history.append({'family':f,'before':current,'after':n});chosen.append(f);current=n
    return chosen,history
