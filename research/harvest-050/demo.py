"""Run a complete local demonstration using only synthetic data and ephemeral keys."""
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import harvest as h, circulation as c, commonwealth as cw, interdependence as id1
import covenant as cv, fellowship as fl, telos as tl, observed, release

def run(directory):
    root=h.real(directory);c.need(not root.exists() and root.parent.is_dir(),'demo requires new directory');root.mkdir();src=root/'source';src.mkdir()
    ks={k:Ed25519PrivateKey.generate() for k in ('alpha','beta','gamma','destination')};trust={k:cv.key(v) for k,v in ks.items()};tp=h.pin(trust);h.write(root/'trust.json',trust)
    issue=release.event([ks['alpha'],ks['destination']],'demo',0,cv.ZERO,0,'issue',dict(creditor=trust['alpha'],debtor=trust['destination'],units=6,expires=20))
    rid=cv.digest(issue);reduction=release.event([ks['alpha']],'demo',1,rid,2,'release',dict(claim=rid,units=2));history=[issue,reduction];head=cv.digest(reduction)
    h.write(src/'obligations.json',history);(src/'recipe.txt').write_bytes(b'productive recipe: 3*x+7\n');(src/'witness.txt').write_bytes(b'An archive can preserve a record without preserving its burden.\n')
    receipt=h.capture(src,root/'capture');m=h.read(root/'capture'/'manifest.json');mp=receipt['manifest_pin'];refs=sorted(c.validate(m));c.need(len(refs)==3,'demo fixture')
    obj={x:cw.read_object(root/'capture'/'objects',x)[0] for x in refs}
    peers={k:root/k for k in ('alpha','beta','gamma')}
    for p in peers.values():p.mkdir()
    cw.save_object(peers['alpha'],refs[0],obj[refs[0]]);cw.save_object(peers['beta'],refs[1],obj[refs[1]])
    eq,parity=id1.equation(obj,{refs[1]:1,refs[2]:1});cw.save_object(peers['gamma'],eq['parity'],parity);records=[eq];rp=h.pin(records);h.write(root/'equations.json',records)
    before={str(p):(c.digest(p.read_bytes()),p.stat().st_mtime_ns) for d in peers.values() for p in d.iterdir()}
    # Actual SN1 field, TL1/FL1 voluntary copy planning. This proposal is not executed.
    ps,report=h.field(m,mp,peers);field=cv.charter_data(refs,tuple(peers),[tl.Asset(1,0,1) for _ in refs],tl.Charter(((0,1),(1,1)),(0,1,2),3,9,2));agree=fl.formation(field,[trust['destination']]*3,[trust[k] for k in peers]);ap=h.pin(agree)
    roles=[ks[k] for k in (*peers,'destination')];endorsements=[fl.endorse(k,agree) for k in roles];chains={};heads={}
    scopes=[('copy',i,a,b) for i in range(3) for a in range(3) for b in range(3) if a!=b]
    for k in roles:
        pub=cv.key(k);ss=[a for a in scopes if pub in {trust['destination'],trust[list(peers)[a[2]]],trust[list(peers)[a[3]]]}];event=fl.offer(k,agree,0,cv.ZERO,0,100,trust['destination'],ss,3);chains[pub]=[event];heads[pub]=cv.digest(event)
    f=fl.Fellowship(agree,endorsements,chains,ap,heads,5);state,op=observed.bind(f,report,mp,0,0);fp=f.plan(trust['destination'],state,[(6,1),(5,1),(3,1)]);p=fl.proposal(ks['destination'],f,state,op,fp['actions'],20);required=f.evaluate(trust['destination'],state,fp['actions'])['required'];signed=[fl.assent(k,p) for k in roles if cv.key(k) in required];fr=fl.verify(f,state,op,p,signed);h.write(root/'cooperation-receipt.json',fr)
    h.write(root/'cooperation-evidence.json',dict(agreement=agree,endorsements=endorsements,chains=chains,heads=heads,proposal=p,assents=signed,observation=report))
    # Operational HV1 route: parity recovery with exact assent from every selected source and destination.
    p=h.plan(m,mp,peers,root/'restored',trust,tp,records,rp);h.write(root/'recovery-plan.json',p);signatures=[h.assent(k,p,100,5) for k in ks.values() if cv.key(k) in p['required_signers']];h.write(root/'assents.json',signatures)
    result=h.restore(m,mp,p,trust,tp,signatures,6,records,rp);h.write(root/'recovery-receipt.json',result)
    history2=h.read(root/'restored'/'obligations.json');past=release.Ledger('demo',history2,head,5).status(rid);present=release.Ledger('demo',history2,head,21).status(rid)
    after={str(p):(c.digest(p.read_bytes()),p.stat().st_mtime_ns) for d in peers.values() for p in d.iterdir()};c.need(before==after and past['outstanding']==4 and present['outstanding']==0,'demo integrity')
    summary=dict(schema='HV1-demo',restoration=result,cooperation_steps=len(fr['steps']),cooperation_executed=False,history_before_expiry=past,history_after_expiry=present,donor_stores_unchanged=True,trust_pin=tp,record_pin=rp)
    h.write(root/'summary.json',summary);return summary
