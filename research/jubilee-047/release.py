"""JB1 signed abstract obligations. Historical records retained; no legal or payment effect.
Trust ledger ID, current head and time externally. No persistence or execution.
"""
import covenant as c
LIMIT=1024

def event(keys,ledger,seq,prev,at,kind,data):
    body=dict(ledger=ledger,seq=seq,prev=prev,at=at,kind=kind,data=data)
    return dict(body=body,signatures=[c.signed(k,dict(issuer=c.key(k),event=c.digest(body)),'jb-event') for k in keys])

class Ledger:
    def __init__(self,ledger,records,head,now):
        c.need(c.ident(ledger) and c.hexstr(head,64) and c.integer(now,0,2**53-1),'trust anchor')
        c.need(isinstance(records,list) and len(records)<=LIMIT,'record limit')
        self.head=c.ZERO;self.now=now;self.claims={};self.history=[];last=0
        for i,r in enumerate(records):
            c.shape(r,'body signatures');b=r['body'];c.shape(b,'ledger seq prev at kind data')
            c.need(b['ledger']==ledger and c.integer(b['seq'],i,i) and b['prev']==self.head and c.integer(b['at'],last,now),'lineage or time');last=b['at'];d=b['data'];kind=b['kind'];rid=c.digest(r)
            if kind=='issue':
                c.shape(d,'creditor debtor units expires');a,z=d['creditor'],d['debtor']
                c.need(c.hexstr(a,64) and c.hexstr(z,64) and a!=z and c.integer(d['units'],1,10000) and (d['expires'] is None or c.integer(d['expires'],last+1,2**53-1)),'issue bounds');required={a,z}
            elif kind in ('release','settle'):
                c.shape(d,'claim units');ref=d['claim'];c.need(c.hexstr(ref,64) and ref in self.claims,'unknown claim');q=self.claims[ref];required={q['creditor']} if kind=='release' else {q['creditor'],q['debtor']}
                c.need((q['expires'] is None or last<q['expires']) and c.integer(d['units'],1,q['remaining']),'expired or excessive reduction')
            else:raise c.Rejected('unknown event')
            ss=r['signatures'];c.need(isinstance(ss,list) and len(ss)==len(required),'signature count');seen=set()
            for s in ss:
                v=c.check(s,'jb-event');c.shape(v,'issuer event');c.need(v['event']==c.digest(b) and v['issuer'] in required and v['issuer'] not in seen,'event assent');seen.add(v['issuer'])
            if kind=='issue':self.claims[rid]=dict(d,remaining=d['units'],released=0,settled=0)
            else:q['remaining']-=d['units'];q['released' if kind=='release' else 'settled']+=d['units']
            self.history.append(rid);self.head=rid
        c.need(self.head==head,'stale head')
    def status(self,ref):
        c.need(ref in self.claims,'unknown claim');q=self.claims[ref];expired=q['expires'] is not None and self.now>=q['expires'];out=0 if expired else q['remaining']
        return dict(q,outstanding=out,expired_units=q['remaining'] if expired else 0)
