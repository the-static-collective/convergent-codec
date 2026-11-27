"""Strict SN1 adapter: one SHA-256-addressed CC1 object per charter asset."""
import covenant as c
import telos as t

def bind(l,report,manifest_pin,public,spent):
    """Derive modeled masks from a trusted complete SN1 report, not ambient paths.
    The caller independently authenticates the report, its freshness and domain mapping.
    Publication and expenditure are externally supplied; SN1 cannot observe them.
    """
    c.need(c.hexstr(manifest_pin,64) and all(c.hexstr(n,64) for n in l.names),'content-addressed asset names required')
    c.need(report['schema']=='SN1' and report['manifest_pin']==manifest_pin and report.get('record_pin') is None and report['mode']=='verify','wrong observation identity or mode')
    c.need(set(report['peers'])==set(l.domains) and report['required_objects']==len(l.names) and report['sampled_objects']==len(l.names),'incomplete observation')
    masks=[0]*len(l.names)
    for i,d in enumerate(l.domains):
        r=report['peers'][d];c.need(r['root_status']=='accessible' and set(r['observations'])==set(l.names),'unavailable or incomplete domain')
        for j,h in enumerate(l.names):
            s=r['observations'][h]['status'];c.need(s in ('verified','missing'),'uncertain or corrupt observation')
            if s=='verified':masks[j]|=1<<i
    s=t.State(tuple(masks),public,spent);c.valid_state(l,s);return s,c.digest(report)
