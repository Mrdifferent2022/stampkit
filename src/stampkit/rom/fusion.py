"""Fusion of analytic and ML results.

Map both models' outputs onto common sample points (nearest-point), then
merge by ML confidence: confident ML wins outright; on strong disagreement,
keep the more conservative (higher-risk) verdict. Phase 4.
"""

from __future__ import annotations

CONFIDENCE_THRESHOLD = 0.7
