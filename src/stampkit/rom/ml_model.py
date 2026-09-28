"""ML classifier for drawing severity (four thinning classes).

Features: drawing depth, mean curvature, thickness, material family. Labels
are thinning ratios normalized by the material's cracking limit. Phase 4.
"""

from __future__ import annotations

import enum


class ThinningClass(enum.IntEnum):
    THICKENING_WRINKLE_RISK = 0
    THINNING_UNDER_HALF_LIMIT = 1
    THINNING_HALF_TO_LIMIT = 2
    CRACK_RISK = 3
