"""Deterministic integer periodic generators. No floating point."""

from typing import List


def generate_periodic(
    sample_count: int,
    period: int,
    amplitude: int,
    phase: int,
    generator_version: int = 1,
) -> List[int]:
    """
    Simple integer square-wave periodic generator.
    Version 1: value = amplitude if ((i + phase) % period) < (period // 2) else -amplitude
    """
    if generator_version != 1:
        raise ValueError(f"unknown generator_version {generator_version}")
    if period <= 0:
        raise ValueError("period must be positive")
    out = []
    half = period // 2
    for i in range(sample_count):
        t = (i + phase) % period
        out.append(amplitude if t < half else -amplitude)
    return out
