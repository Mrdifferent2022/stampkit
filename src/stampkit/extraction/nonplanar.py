"""Non-planar feature extraction.

Sew intersecting non-planar faces into open shells; classify by planar-face
intersection count (bends standalone, embosses touch one plane, drawings span
several) and by boundary-curve count (emboss vs extruded hole).
Phase 1 implements bends; Phase 2 the rest.
"""

from __future__ import annotations
