"""ZigZag + unsigned varint encoding/decoding. Deterministic, pure integer, minimal encoding enforced."""

from typing import List, Tuple
from .errors import CodecFormatError


def zigzag_encode(n: int) -> int:
    """Map signed integer to unsigned for varint."""
    return (n << 1) ^ (n >> 63)


def zigzag_decode(n: int) -> int:
    return (n >> 1) ^ (-(n & 1))


def write_uvarint(value: int) -> bytes:
    if value < 0:
        raise CodecFormatError("uvarint requires non-negative")
    out = bytearray()
    while value >= 0x80:
        out.append((value & 0x7F) | 0x80)
        value >>= 7
    out.append(value)
    return bytes(out)


def read_uvarint(data: bytes, offset: int = 0) -> Tuple[int, int]:
    """Read uvarint and enforce minimal (canonical) encoding."""
    result = 0
    shift = 0
    pos = offset
    while True:
        if pos >= len(data):
            raise CodecFormatError("truncated varint")
        b = data[pos]
        pos += 1
        result |= (b & 0x7F) << shift
        if (b & 0x80) == 0:
            break
        shift += 7
        if shift > 63:
            raise CodecFormatError("varint too long")
    consumed = data[offset:pos]
    if consumed != write_uvarint(result):
        raise CodecFormatError("non-canonical varint")
    return result, pos


def write_zigzag_varint(n: int) -> bytes:
    return write_uvarint(zigzag_encode(n))


def read_zigzag_varint(data: bytes, offset: int = 0) -> Tuple[int, int]:
    u, pos = read_uvarint(data, offset)
    return zigzag_decode(u), pos


def write_zigzag_stream(values: List[int]) -> bytes:
    return b"".join(write_zigzag_varint(v) for v in values)


def read_zigzag_stream(data: bytes, count: int, offset: int = 0) -> Tuple[List[int], int]:
    values = []
    pos = offset
    for _ in range(count):
        v, pos = read_zigzag_varint(data, pos)
        values.append(v)
    return values, pos
