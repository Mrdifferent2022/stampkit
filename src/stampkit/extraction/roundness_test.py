"""Hole-vs-slot discrimination via the roundness ratio.

A closed planar curve is a hole iff area / d^2 == pi, where d is the distance
from the centroid to the closest outline point. Phase 1.
"""

from __future__ import annotations

import math

_ROUNDNESS_TOL = 0.05


def is_round(area: float, centroid_to_outline_dist: float, *, tol: float = _ROUNDNESS_TOL) -> bool:
    if centroid_to_outline_dist <= 0:
        return False
    ratio = area / (centroid_to_outline_dist**2)
    return abs(ratio - math.pi) / math.pi < tol
