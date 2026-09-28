"""Analytic simplified stamping analysis.

Section the drawing feature into 2D splines; under plane-strain and fixed
end-point assumptions, the per-segment length ratio gives the principal
logarithmic strain, and volume constancy gives the final thickness. Phase 4.
"""

from __future__ import annotations

import math


def principal_strain(original: float, deformed: float) -> float:
    """Logarithmic strain eps = ln(L / L0)."""
    if original <= 0 or deformed <= 0:
        raise ValueError("lengths must be positive")
    return math.log(deformed / original)


def thinning_ratio(thickness0: float, strain: float) -> float:
    """Relative thickness change after deformation, from volume constancy."""
    return 1.0 - thickness0 * math.exp(-strain) / thickness0 if strain else 0.0
