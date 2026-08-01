"""Frame serialization and deserialization. Engine owns measurement; frames are pure executable."""

from typing import List, Tuple
from enum import IntEnum
from . import varint
from .canonical import (
    source_sha256, pack_mask, unpack_mask, require_int32, require_canonical_mask_padding,
)
from .generators import generate_periodic
from .errors import CodecFormatError
from .limits import (
    MAX_FRAME_BYTES, MAX_SAMPLES_PER_FRAME, MAX_PERIOD, MAX_MASK_BYTES,
)


class Family(IntEnum):
    RAW = 0
    PERIODIC_SPARSE = 1


RESIDUAL_NONE = 0
RESIDUAL_NON_ANOMALY = 1
RESIDUAL_DENSE = 2

VERSION = 1


def serialize_raw(values: List[int]) -> bytes:
    require_int32(values)
    if len(values) > MAX_SAMPLES_PER_FRAME:
        raise CodecFormatError("sample count exceeds format limit")
    digest = source_sha256(values)
    parts = [
        bytes([VERSION, Family.RAW]),
        varint.write_uvarint(len(values)),
        varint.write_zigzag_stream(values),
        digest,
    ]
    frame = b"".join(parts)
    if len(frame) > MAX_FRAME_BYTES:
        raise CodecFormatError("frame exceeds maximum size")
    return frame


def serialize_periodic_sparse(
    values: List[int],
    period: int,
    amplitude: int,
    phase: int,
    generator_version: int,
    anomaly_mask: List[bool],
    anomaly_values: List[int],
    residuals: List[int],
    residual_mode: int = RESIDUAL_NON_ANOMALY,
) -> bytes:
    require_int32(values)
    n = len(values)
    if n > MAX_SAMPLES_PER_FRAME:
        raise CodecFormatError("sample count exceeds format limit")
    if period < 1 or period > MAX_PERIOD:
        raise CodecFormatError("period outside permitted range")
    if n != len(anomaly_mask):
        raise CodecFormatError("anomaly_mask length mismatch")
    n_anom = sum(1 for b in anomaly_mask if b)
    if len(anomaly_values) != n_anom:
        raise CodecFormatError("anomaly_values count mismatch")

    if residual_mode == RESIDUAL_NONE:
        if any(r != 0 for r in residuals):
            raise CodecFormatError("RESIDUAL_NONE requires all residuals zero")
        residual_stream = []
    elif residual_mode == RESIDUAL_NON_ANOMALY:
        residual_stream = [residuals[i] for i in range(n) if not anomaly_mask[i]]
    elif residual_mode == RESIDUAL_DENSE:
        residual_stream = residuals
        if len(residual_stream) != n:
            raise CodecFormatError("dense residual count mismatch")
    else:
        raise CodecFormatError(f"unknown residual_mode {residual_mode}")

    digest = source_sha256(values)
    mask_bytes = pack_mask(anomaly_mask)
    require_canonical_mask_padding(mask_bytes, n)

    parts = [
        bytes([VERSION, Family.PERIODIC_SPARSE]),
        varint.write_uvarint(n),
        varint.write_uvarint(period),
        varint.write_zigzag_varint(amplitude),
        varint.write_uvarint(phase),
        bytes([generator_version, residual_mode]),
        mask_bytes,
        varint.write_zigzag_stream(anomaly_values),
        varint.write_zigzag_stream(residual_stream),
        digest,
    ]
    frame = b"".join(parts)
    if len(frame) > MAX_FRAME_BYTES:
        raise CodecFormatError("frame exceeds maximum size")
    return frame


def deserialize(frame: bytes) -> Tuple[List[int], Family]:
    try:
        return _deserialize_inner(frame)
    except CodecFormatError:
        raise
    except (IndexError, ValueError, OverflowError) as e:
        raise CodecFormatError(str(e)) from e


def _deserialize_inner(frame: bytes) -> Tuple[List[int], Family]:
    if len(frame) > MAX_FRAME_BYTES:
        raise CodecFormatError("frame exceeds maximum size")
    if len(frame) < 3:
        raise CodecFormatError("frame too short")

    pos = 0
    version = frame[pos]; pos += 1
    if version != VERSION:
        raise CodecFormatError(f"unknown version {version}")
    family_val = frame[pos]; pos += 1
    try:
        family = Family(family_val)
    except ValueError:
        raise CodecFormatError(f"unknown family {family_val}")

    sample_count, pos = varint.read_uvarint(frame, pos)
    if sample_count > MAX_SAMPLES_PER_FRAME:
        raise CodecFormatError("sample count exceeds format limit")

    if family == Family.RAW:
        values, pos = varint.read_zigzag_stream(frame, sample_count, pos)
        if pos + 32 != len(frame):
            raise CodecFormatError("trailing or missing bytes in RAW frame")
        digest = frame[pos:pos+32]
        require_int32(values)
        if digest != source_sha256(values):
            raise CodecFormatError("source_sha256 mismatch")
        return values, family

    if family == Family.PERIODIC_SPARSE:
        period, pos = varint.read_uvarint(frame, pos)
        if period < 1 or period > MAX_PERIOD:
            raise CodecFormatError("period outside permitted range")
        amplitude, pos = varint.read_zigzag_varint(frame, pos)
        phase, pos = varint.read_uvarint(frame, pos)

        if pos >= len(frame):
            raise CodecFormatError("truncated generator version")
        generator_version = frame[pos]; pos += 1
        if pos >= len(frame):
            raise CodecFormatError("truncated residual_mode")
        residual_mode = frame[pos]; pos += 1

        mask_nbytes = (sample_count + 7) // 8
        if mask_nbytes > MAX_MASK_BYTES:
            raise CodecFormatError("mask exceeds maximum size")
        if pos + mask_nbytes > len(frame):
            raise CodecFormatError("truncated mask")
        mask_bytes = frame[pos:pos+mask_nbytes]
        pos += mask_nbytes
        anomaly_mask = unpack_mask(mask_bytes, sample_count)
        n_anom = sum(1 for b in anomaly_mask if b)

        anomaly_values, pos = varint.read_zigzag_stream(frame, n_anom, pos)

        if residual_mode == RESIDUAL_NONE:
            residuals = [0] * sample_count
        elif residual_mode == RESIDUAL_NON_ANOMALY:
            residual_stream, pos = varint.read_zigzag_stream(frame, sample_count - n_anom, pos)
            residuals = [0] * sample_count
            r_idx = 0
            for i in range(sample_count):
                if not anomaly_mask[i]:
                    residuals[i] = residual_stream[r_idx]
                    r_idx += 1
        elif residual_mode == RESIDUAL_DENSE:
            residual_stream, pos = varint.read_zigzag_stream(frame, sample_count, pos)
            residuals = residual_stream
        else:
            raise CodecFormatError(f"unknown residual_mode {residual_mode}")

        if pos + 32 != len(frame):
            raise CodecFormatError("trailing or missing bytes in PERIODIC_SPARSE frame")
        digest = frame[pos:pos+32]

        g = generate_periodic(sample_count, period, amplitude, phase, generator_version)
        a = [0] * sample_count
        av_idx = 0
        for i, bit in enumerate(anomaly_mask):
            if bit:
                a[i] = anomaly_values[av_idx]
                av_idx += 1
        values = [g[i] + a[i] + residuals[i] for i in range(sample_count)]

        require_int32(values)
        if digest != source_sha256(values):
            raise CodecFormatError("source_sha256 mismatch after reconstruction")
        return values, family

    raise CodecFormatError(f"unknown family {family}")
