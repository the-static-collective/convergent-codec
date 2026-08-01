"""Canonical serialization helpers, Int32 contract, mask padding, and source digest."""

import hashlib
from typing import List, Sequence
from .errors import CodecFormatError
from .limits import MAX_SAMPLES_PER_FRAME

INT32_MIN = -(1 << 31)
INT32_MAX = (1 << 31) - 1


def require_int32(values: Sequence[int]) -> None:
    for i, value in enumerate(values):
        if not isinstance(value, int) or not (INT32_MIN <= value <= INT32_MAX):
            raise CodecFormatError(f"sample {i} outside signed Int32 range: {value}")


def source_sha256(values: List[int]) -> bytes:
    buf = bytearray()
    for v in values:
        buf.extend(v.to_bytes(4, "little", signed=True))
    return hashlib.sha256(buf).digest()


def pack_mask(mask: List[bool]) -> bytes:
    n = len(mask)
    nbytes = (n + 7) // 8
    out = bytearray(nbytes)
    for i, bit in enumerate(mask):
        if bit:
            out[i // 8] |= 1 << (i % 8)
    return bytes(out)


def require_canonical_mask_padding(mask_bytes: bytes, sample_count: int) -> None:
    """Unused high bits of the final mask byte must be zero."""
    if sample_count == 0:
        if mask_bytes:
            raise CodecFormatError("mask must be empty for zero samples")
        return
    remainder = sample_count % 8
    if remainder == 0:
        return
    if not mask_bytes:
        raise CodecFormatError("missing mask bytes")
    allowed_low_bits = (1 << remainder) - 1
    padding_bits = mask_bytes[-1] & ~allowed_low_bits
    if padding_bits != 0:
        raise CodecFormatError("non-canonical mask padding")


def unpack_mask(data: bytes, count: int) -> List[bool]:
    expected = (count + 7) // 8
    if len(data) < expected:
        raise CodecFormatError("truncated mask")
    require_canonical_mask_padding(data[:expected], count)
    mask = []
    for i in range(count):
        byte = data[i // 8]
        bit = (byte >> (i % 8)) & 1
        mask.append(bool(bit))
    return mask
