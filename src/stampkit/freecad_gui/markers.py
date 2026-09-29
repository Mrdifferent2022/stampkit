"""3D text markers for features, drawn with pivy/coin (GUI only).

Each marker is an SoAnnotation node (screen-aligned text, always on top)
placed at the centroid of the feature's faces. Markers are tracked per
document so they can be removed on clear/re-evaluate.
"""

from __future__ import annotations

from stampkit.report.schema import Report

#: (text, position xyz, rgb) triple.
Marker = tuple[str, tuple[float, float, float], tuple[float, float, float]]

# fix features sit on red-highlighted faces, so their labels must be white;
# accept features usually sit on gray faces, where yellow reads well.
_FIX_RGB = (1.0, 1.0, 1.0)
_OK_RGB = (1.0, 0.85, 0.2)

_INSERTED: dict[str, list[tuple[object, object]]] = {}  # doc name -> (root, node)


def _face_index(ref: str) -> int | None:
    try:
        return int(ref.split(":", 1)[1])
    except (IndexError, ValueError):
        return None


def _feature_anchor(shape: object, face_refs: list[str]) -> tuple[float, float, float] | None:
    pts = []
    faces = shape.Faces
    for ref in face_refs:
        idx = _face_index(ref)
        if idx is not None and 0 <= idx < len(faces):
            c = faces[idx].CenterOfMass
            pts.append((c.x, c.y, c.z))
    if not pts:
        return None
    n = len(pts)
    return (
        sum(p[0] for p in pts) / n,
        sum(p[1] for p in pts) / n,
        sum(p[2] for p in pts) / n,
    )


def build_markers(shape: object, report: Report) -> list[Marker]:
    """One marker per feature at its anchor, red for fix, yellow otherwise."""
    fix_ids = {f.feature_id for f in report.findings if f.verdict == "fix"}
    markers: list[Marker] = []
    for feat in report.features:
        if feat.anchor is not None and len(feat.anchor) == 3:
            anchor = (feat.anchor[0], feat.anchor[1], feat.anchor[2])
        else:
            anchor = _feature_anchor(shape, feat.face_refs)
        if anchor is not None:
            rgb = _FIX_RGB if feat.id in fix_ids else _OK_RGB
            markers.append((feat.id, anchor, rgb))
    return markers


def _scene_root(view: object) -> object:
    try:
        return view.getSceneGraph()
    except AttributeError:
        return view.getViewer().getSoRenderManager().getSceneGraph()


def show_markers(doc_name: str, view: object, markers: list[Marker]) -> int:
    """Insert markers into the view's scenegraph; returns how many."""
    from pivy import coin  # type: ignore[import-not-found]

    clear_markers(doc_name)
    root = _scene_root(view)
    inserted: list[tuple[object, object]] = []
    for text, pos, rgb in markers:
        ann = coin.SoAnnotation()
        trans = coin.SoTranslation()
        trans.translation.setValue(pos[0], pos[1], pos[2])
        font = coin.SoFont()
        font.size.setValue(13)
        ann.addChild(trans)
        ann.addChild(font)
        # drop shadow first (readable over bright hole voids), colored on top
        offset = coin.SoTranslation()
        offset.translation.setValue(0.35, 0.35, 0.0)
        shadow_color = coin.SoBaseColor()
        shadow_color.rgb.setValue((0.05, 0.05, 0.05))
        shadow = coin.SoText2()
        shadow.string.setValue(text)
        shadow.justification = coin.SoText2.CENTER
        ann.addChild(offset)
        ann.addChild(shadow_color)
        ann.addChild(shadow)
        back = coin.SoTranslation()
        back.translation.setValue(-0.35, -0.35, 0.0)
        color = coin.SoBaseColor()
        color.rgb.setValue(rgb)
        label = coin.SoText2()
        label.string.setValue(text)
        label.justification = coin.SoText2.CENTER
        ann.addChild(back)
        ann.addChild(color)
        ann.addChild(label)
        root.addChild(ann)
        inserted.append((root, ann))
    _INSERTED[doc_name] = inserted
    return len(inserted)


def clear_markers(doc_name: str) -> None:
    import contextlib

    for root, node in _INSERTED.pop(doc_name, []):
        with contextlib.suppress(Exception):  # document/view already gone
            root.removeChild(node)


def marker_count(doc_name: str) -> int:
    return len(_INSERTED.get(doc_name, []))
