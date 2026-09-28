"""Contour-line (hatch) machinery.

Generate parallel hatch lines over a face's bounding surface, trim them
against the face, eliminate interference, and detect crossing-line clusters
that mark outline features (notches / projections). Phase 2.
"""

from __future__ import annotations
