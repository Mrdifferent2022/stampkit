"""Thickness-removal strategies.

Three strategies in priority order:
  (a) large-face pairing by area ranking and opposing normals (fast path);
  (b) midsurface/offset attempt via the kernel;
  (c) fallback: keep the full solid and treat thin side-wall faces (one
      dimension ~= thickness) as blank edges.

Phase 1 selects empirically on the golden test parts.
"""

from __future__ import annotations

import enum


class ThicknessStrategy(enum.StrEnum):
    FACE_PAIRING = "face_pairing"
    MIDSURFACE = "midsurface"
    THIN_WALL_FALLBACK = "thin_wall_fallback"


def select_strategy(*args: object, **kwargs: object) -> ThicknessStrategy:
    raise NotImplementedError("lands in Phase 1")
