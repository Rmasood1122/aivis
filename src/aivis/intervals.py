"""Wilson score interval. Canonical product copy (wilson-v1, 2026-09-01).

Signature matches caai_v2_scorer.wilson: (point, low, high) as proportions.
n=0 raises: a rate with no denominator has no interval -- the caller
abstains, it does not receive (0, 0, 0) to print as a finding.
"""
from __future__ import annotations

import math

Z_95 = 1.959963984540054


def wilson(successes: int, n: int, z: float = Z_95) -> tuple[float, float, float]:
    if n <= 0:
        raise ValueError("wilson: n must be positive; abstain instead of estimating")
    if not 0 <= successes <= n:
        raise ValueError(f"wilson: successes {successes} outside [0, {n}]")
    p = successes / n
    z2 = z * z
    denom = 1.0 + z2 / n
    centre = (p + z2 / (2.0 * n)) / denom
    half = (z / denom) * math.sqrt(p * (1.0 - p) / n + z2 / (4.0 * n * n))
    return (p, max(0.0, centre - half), min(1.0, centre + half))
