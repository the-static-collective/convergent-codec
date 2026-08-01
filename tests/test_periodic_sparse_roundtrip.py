from convergent_codec import encode, decode
from convergent_codec.generators import generate_periodic


def test_pure_periodic():
    period, amp, phase = 8, 10, 0
    vals = generate_periodic(64, period, amp, phase, 1)
    c = encode(vals)
    assert decode(c.frame) == vals


def test_periodic_with_anomalies():
    period, amp, phase = 10, 20, 2
    vals = generate_periodic(40, period, amp, phase, 1)
    vals[5] += 100
    vals[17] -= 50
    vals[33] += 7
    c = encode(vals)
    assert decode(c.frame) == vals


def test_random_falls_to_raw():
    import random
    random.seed(42)
    vals = [random.randint(-1000, 1000) for _ in range(50)]
    c = encode(vals)
    assert decode(c.frame) == vals
