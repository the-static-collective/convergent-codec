import pytest
from convergent_codec import encode, CodecFormatError
from convergent_codec.frames import deserialize, serialize_periodic_sparse, RESIDUAL_NONE
from convergent_codec.generators import generate_periodic


def test_truncated_rejected():
    c = encode([1, 2, 3])
    with pytest.raises(CodecFormatError):
        deserialize(c.frame[:-5])


def test_trailing_bytes_rejected():
    c = encode([1, 2, 3])
    with pytest.raises(CodecFormatError):
        deserialize(c.frame + b"\x00")


def test_wrong_digest_rejected():
    c = encode([10, 20, 30])
    bad = bytearray(c.frame)
    bad[-1] ^= 0xFF
    with pytest.raises(CodecFormatError):
        deserialize(bytes(bad))


def test_unknown_version_rejected():
    c = encode([1])
    bad = bytearray(c.frame)
    bad[0] = 99
    with pytest.raises(CodecFormatError):
        deserialize(bytes(bad))


def test_out_of_range_int32_rejected():
    with pytest.raises(CodecFormatError):
        encode([2**31])
    with pytest.raises(CodecFormatError):
        encode([-(2**31) - 1])


def test_non_canonical_mask_padding_rejected():
    vals = generate_periodic(9, 4, 5, 0, 1)
    mask = [False] * 9
    mask[0] = True
    frame = serialize_periodic_sparse(
        vals, 4, 5, 0, 1, mask, [vals[0] - 5], [0]*9, residual_mode=RESIDUAL_NONE
    )
    bad = bytearray(frame)
    mask_start = 8
    bad[mask_start + 1] |= 0xFE
    with pytest.raises(CodecFormatError, match="non-canonical mask padding"):
        deserialize(bytes(bad))
