"""RAW model: always-available baseline. Supplies frame only; engine measures cost."""

from typing import List, Dict, Any
from ..frames import serialize_raw, Family
from ..canonical import require_int32


def propose(values: List[int]) -> Dict[str, Any]:
    require_int32(values)
    frame = serialize_raw(values)
    return {
        "family": Family.RAW,
        "frame": frame,
        "evidence": {"note": "universal fallback"},
    }
