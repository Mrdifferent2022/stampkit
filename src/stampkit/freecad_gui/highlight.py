"""Map findings to faces and highlight them in the 3D view.

Highlighting recolors the faces of features with a "fix" verdict red and
remembers the object's original per-face colors so they can be restored.
Only ever called in GUI mode.
"""

from __future__ import annotations

from stampkit.report.schema import Report

_FIX_COLOR = (0.90, 0.15, 0.15, 0.0)
_ORIGINAL_COLORS: dict[str, list] = {}


def _face_index(ref: str) -> int | None:
    try:
        return int(ref.split(":", 1)[1])
    except (IndexError, ValueError):
        return None


def apply_highlights(view_obj: object, report: Report, face_count: int) -> int:
    """Recolor fix-verdict faces of view_obj; returns the highlighted count."""
    fix_ids = {f.feature_id for f in report.findings if f.verdict == "fix"}
    if not fix_ids:
        return 0
    key = f"{view_obj.Object.Document.Name}#{view_obj.Object.Name}"
    if key not in _ORIGINAL_COLORS:
        _ORIGINAL_COLORS[key] = list(view_obj.DiffuseColor)
    base = _ORIGINAL_COLORS[key]
    if len(base) != face_count:
        base = [base[0]] * face_count if base else [(0.8, 0.8, 0.8, 0.0)] * face_count
    colors = list(base)
    highlighted = 0
    for feat in report.features:
        if feat.id not in fix_ids:
            continue
        for ref in feat.face_refs:
            idx = _face_index(ref)
            if idx is not None and 0 <= idx < face_count:
                colors[idx] = _FIX_COLOR
                highlighted += 1
    view_obj.DiffuseColor = colors
    return highlighted


def clear_highlights(view_obj: object) -> None:
    """Restore the object's original colors, if it was highlighted."""
    key = f"{view_obj.Object.Document.Name}#{view_obj.Object.Name}"
    original = _ORIGINAL_COLORS.pop(key, None)
    if original is not None:
        view_obj.DiffuseColor = original


def clear_all(document: object) -> None:
    for obj in document.Objects:
        view_obj = getattr(obj, "ViewObject", None)
        if view_obj is not None:
            clear_highlights(view_obj)
