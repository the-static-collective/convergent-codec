"""PERIODIC_SPARSE model. Supplies frame only; engine measures cost and verifies."""

from typing import List, Tuple, Dict, Any, Optional
from ..frames import serialize_periodic_sparse, Family, RESIDUAL_NONE, RESIDUAL_NON_ANOMALY
from ..generators import generate_periodic
from ..canonical import require_int32


def detect_period_amplitude(values: List[int], max_period: int = 64) -> Tuple[int, int, int]:
    """Improved integer estimator: median of values[i] * expected_sign(i)."""
    n = len(values)
    if n == 0:
        return 1, 0, 0
    best = (1, 0, 0, float("inf"))
    for period in range(1, min(max_period, n) + 1):
        for phase in range(period):
            half = period // 2 or 1
            signed_amps = []
            for i in range(n):
                t = (i + phase) % period
                expected_sign = 1 if t < half else -1
                signed_amps.append(values[i] * expected_sign)
            if not signed_amps:
                amp = 0
            else:
                signed_amps.sort()
                amp = signed_amps[len(signed_amps) // 2]
            g = generate_periodic(n, period, amp, phase, 1)
            residual_energy = sum((values[i] - g[i]) ** 2 for i in range(n))
            if residual_energy < best[3]:
                best = (period, amp, phase, residual_energy)
    return best[0], best[1], best[2]


def propose(values: List[int]) -> Optional[Dict[str, Any]]:
    require_int32(values)
    n = len(values)
    if n < 4:
        return None
    period, amplitude, phase = detect_period_amplitude(values)
    g = generate_periodic(n, period, amplitude, phase, 1)

    thresh = max(1, abs(amplitude) // 4)
    anomaly_mask = []
    anomaly_values = []
    residuals = []
    for i in range(n):
        r = values[i] - g[i]
        if abs(r) > thresh:
            anomaly_mask.append(True)
            anomaly_values.append(r)
            residuals.append(0)
        else:
            anomaly_mask.append(False)
            residuals.append(r)

    if all(r == 0 for r in residuals):
        residual_mode = RESIDUAL_NONE
    else:
        residual_mode = RESIDUAL_NON_ANOMALY

    frame = serialize_periodic_sparse(
        values, period, amplitude, phase, 1,
        anomaly_mask, anomaly_values, residuals, residual_mode
    )
    return {
        "family": Family.PERIODIC_SPARSE,
        "frame": frame,
        "evidence": {
            "period": period,
            "amplitude": amplitude,
            "phase": phase,
            "n_anomalies": len(anomaly_values),
            "residual_mode": residual_mode,
        },
    }
