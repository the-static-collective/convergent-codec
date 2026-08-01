"""Thin public decoder entry point."""

from typing import List
from .frames import deserialize


def decode_frame(frame: bytes) -> List[int]:
    values, _ = deserialize(frame)
    return values
