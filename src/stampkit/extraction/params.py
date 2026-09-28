"""Geometric parameter computation.

Hole diameter via the longest control-point-pair chord; slot/notch/projection
length & width via bounding-box extents; pairwise feature and feature-to-edge
minimum distances (precomputed and stored in feature params). Phase 1.
"""

from __future__ import annotations
