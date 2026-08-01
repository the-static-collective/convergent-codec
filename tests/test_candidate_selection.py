from convergent_codec import encode, decode, WitnessLedger, ProposalDisposition
from convergent_codec.frames import Family, serialize_raw
from convergent_codec.models import raw


def test_winner_exact_bits_equals_frame_len():
    vals = list(range(20))
    c = encode(vals)
    assert c.exact_bits == len(c.frame) * 8
    assert decode(c.frame) == vals


def test_raw_always_available_and_correct():
    vals = [1, -2, 3, -4, 5]
    prop = raw.propose(vals)
    from convergent_codec.frames import deserialize
    decoded, fam = deserialize(prop["frame"])
    assert decoded == vals and fam == Family.RAW


def test_winner_never_worse_than_raw():
    for n in [0, 1, 8, 16, 32, 64]:
        vals = list(range(n))
        c = encode(vals)
        raw_bits = len(serialize_raw(vals)) * 8
        assert c.exact_bits <= raw_bits


def test_witness_disposition_states():
    vals = list(range(16))
    ledger = WitnessLedger()
    c = encode(vals, ledger=ledger)
    dispositions = {e.disposition for e in ledger.entries}
    assert ProposalDisposition.SELECTED in dispositions
    selected = [e for e in ledger.entries if e.disposition == ProposalDisposition.SELECTED]
    assert len(selected) == 1
    assert selected[0].family == c.family.name
