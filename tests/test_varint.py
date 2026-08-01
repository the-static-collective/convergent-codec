from convergent_codec.varint import (
    zigzag_encode, zigzag_decode,
    write_uvarint, read_uvarint,
    write_zigzag_varint, read_zigzag_varint,
    write_zigzag_stream, read_zigzag_stream,
)


def test_zigzag_roundtrip():
    for n in [0, 1, -1, 2, -2, 127, -128, 1000, -1000, 2**31-1, -2**31]:
        assert zigzag_decode(zigzag_encode(n)) == n


def test_uvarint_roundtrip():
    for n in [0, 1, 127, 128, 255, 16384, 2**20]:
        b = write_uvarint(n)
        v, pos = read_uvarint(b)
        assert v == n and pos == len(b)


def test_stream():
    vals = [0, -1, 42, -100, 100000]
    b = write_zigzag_stream(vals)
    out, pos = read_zigzag_stream(b, len(vals))
    assert out == vals and pos == len(b)
