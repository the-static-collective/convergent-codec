from convergent_codec import encode, decode
from convergent_codec.frames import Family


def test_empty():
    c = encode([])
    assert decode(c.frame) == []
    assert c.family == Family.RAW


def test_single():
    for v in [0, 1, -1, 42, -42]:
        c = encode([v])
        assert decode(c.frame) == [v]


def test_int32_extremes():
    vals = [-2**31, 2**31-1, 0, -1, 1]
    c = encode(vals)
    assert decode(c.frame) == vals


def test_alternating_signs():
    vals = [i if i % 2 == 0 else -i for i in range(32)]
    c = encode(vals)
    assert decode(c.frame) == vals


def test_non64_length():
    for n in [1, 3, 7, 15, 33, 100]:
        vals = list(range(n))
        c = encode(vals)
        assert decode(c.frame) == vals
