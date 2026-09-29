"""Map findings to faces and highlight them in the 3D view.

Highlighting recolors the faces of features with a "fix" verdict red and
remembers the object's original per-face colors so they can be restored.
Only ever called in GUI mode.

Color tuples keep the object's own alpha channel: FreeCAD treats the 4th
component as opacity (1.0 = opaque), so a hardcoded 0.0 alpha would paint
the violating faces transparent instead of red.
"""

from __future__ import annotations

from stampkit.report.schema import Report

_FIX_RGB = (0.90, 0.15, 0.15)
_FALLBACK_COLOR = (0.8, 0.8, 0.8, 1.0)
_ORIGINAL_COLORS: dict[str, list] = {}


def _face_index(ref: str) -> int | None:
    try:
        return int(ref.split(":", 1)[1])
    except (IndexError, ValueError):
        return None


def _key(view_obj: object) -> str:
    return f"{view_obj.Object.Document.Name}#{view_obj.Object.Name}"


def _template_color(view_obj: object) -> tuple:
    """The object's uniform color, used as the per-face template."""
    diffuse = list(getattr(view_obj, "DiffuseColor", None) or [])
    if diffuse:
        return tuple(diffuse[0])
    shape_color = getattr(view_obj, "ShapeColor", None)
    if shape_color:
        return tuple(shape_color)
    return _FALLBACK_COLOR


def _with_rgb(template: tuple, rgb: tuple[float, float, float]) -> tuple:
    """rgb with the template's alpha/length (3- and 4-tuples supported)."""
    if len(template) >= 4:
        return (rgb[0], rgb[1], rgb[2], template[3])
    return (rgb[0], rgb[1], rgb[2])


def apply_highlights(view_obj: object, report: Report, face_count: int) -> int:
    """Recolor fix-verdict faces of view_obj; returns the highlighted count."""
    fix_ids = {f.feature_id for f in report.findings if f.verdict == "fix"}
    if not fix_ids:
        return 0
    key = _key(view_obj)
    if key not in _ORIGINAL_COLORS:
        _ORIGINAL_COLORS[key] = list(view_obj.DiffuseColor)
    template = _template_color(view_obj)
    colors = [template] * face_count
    fix_color = _with_rgb(template, _FIX_RGB)
    highlighted = 0
    for feat in report.features:
        if feat.id not in fix_ids:
            continue
        for ref in feat.face_refs:
            idx = _face_index(ref)
            if idx is not None and 0 <= idx < face_count:
                colors[idx] = fix_color
                highlighted += 1
    view_obj.DiffuseColor = colors
    return highlighted


def clear_highlights(view_obj: object) -> None:
    """Restore the object's original colors, if it was highlighted."""
    key = _key(view_obj)
    original = _ORIGINAL_COLORS.pop(key, None)
    if original is not None:
        view_obj.DiffuseColor = original


def clear_all(document: object) -> None:
    for obj in document.Objects:
        view_obj = getattr(obj, "ViewObject", None)
        if view_obj is not None:
            clear_highlights(view_obj)


def select_feature(obj: object, feature: object) -> int:
    """Natively select a feature's faces in the 3D view; returns the count.

    FreeCAD sub-element names are 1-based ("Face1" == Shape.Faces[0]).
    """
    import FreeCADGui as Gui  # type: ignore[import-not-found]

    names = []
    for ref in feature.face_refs:
        idx = _face_index(ref)
        if idx is not None and 0 <= idx < len(obj.Shape.Faces):
            names.append(f"Face{idx + 1}")
    Gui.Selection.clearSelection()
    for name in names:
        Gui.Selection.addSelection(obj.Document.Name, obj.Name, name)
    return len(names)


def clear_selection() -> None:
    import FreeCADGui as Gui  # type: ignore[import-not-found]

    Gui.Selection.clearSelection()
