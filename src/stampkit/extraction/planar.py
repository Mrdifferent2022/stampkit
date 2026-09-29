"""Planar-face feature extraction.

- Holes/slots from inner wires + roundness discrimination (Phase 1);
- Notches/projections from outer-wire channel detection (Phase 2);
- Relief-cuts are reclassified notches near bend tangent edges (pipeline).
"""

from __future__ import annotations

from stampkit.extraction import outline
from stampkit.extraction.kernel import GeometryKernel, ShapeRef
from stampkit.extraction.roundness_test import is_round
from stampkit.extraction.thickness import frame_axes, project_to_plane
from stampkit.model.context import KernelSettings
from stampkit.model.features import Feature, FeatureKind
from stampkit.model.geometry import Point3

#: (feature, host wire, host sheet-face index) — handles stay inside extraction.
PlanarHit = tuple[Feature, ShapeRef, int]


def _face_refs(face_idx: int, partners: dict[int, list[int]] | None) -> tuple[str, ...]:
    """Refs for the representative face plus the other side(s) of its wall."""
    refs = [f"face:{face_idx}"]
    refs += [f"face:{p}" for p in (partners or {}).get(face_idx, [])]
    return tuple(refs)


def extract_planar_features(
    kernel: GeometryKernel,
    sheet_faces: list[tuple[int, ShapeRef]],
    partners: dict[int, list[int]] | None = None,
) -> list[PlanarHit]:
    hits: list[PlanarHit] = []
    counters: dict[FeatureKind, int] = {}
    for face_idx, face in sheet_faces:
        _outer, inners = kernel.wires(face)
        for wire in inners:
            if not kernel.is_closed(wire):
                continue
            area = kernel.area_of_wire(wire, face)
            centroid = kernel.centroid_of_wire(wire, face)
            d = kernel.closest_dist_to_wire(wire, centroid)
            kind = FeatureKind.HOLE if is_round(area, d) else FeatureKind.SLOT
            counters[kind] = counters.get(kind, 0) + 1
            feature = Feature(
                id=f"{kind.value}{counters[kind]}",
                kind=kind,
                face_refs=_face_refs(face_idx, partners),
                anchor=centroid,
                params={"area_mm2": area},
            )
            hits.append((feature, wire, face_idx))
    return hits


def extract_outline_features(
    kernel: GeometryKernel,
    sheet_faces: list[tuple[int, ShapeRef]],
    settings: KernelSettings,
    partners: dict[int, list[int]] | None = None,
) -> list[tuple[Feature, int, Point3]]:
    """Detect notches/projections on sheet-face outlines.

    Returns (feature, host face index, 3D mouth midpoint) triples. The mouth
    position is needed later for relief-cut reclassification.
    """
    results: list[tuple[Feature, int, Point3]] = []
    counters: dict[FeatureKind, int] = {}
    for face_idx, face in sheet_faces:
        outer, _inner = kernel.wires(face)
        poly = kernel.discretize(outer, settings.discretization_tol_mm)
        frame = kernel.plane_frame(face)
        u, v = frame_axes(frame)
        pts = poly.points
        if len(pts) > 1 and pts[0].distance_to(pts[-1]) < settings.discretization_tol_mm:
            pts = pts[:-1]
        pts2d = outline.densify([project_to_plane(p, frame, u, v) for p in pts])
        for ch in outline.find_channels(
            pts2d,
            max_width_mm=settings.channel_max_width_mm,
            max_depth_mm=settings.channel_max_depth_mm,
        ):
            kind = FeatureKind.NOTCH if ch.kind == "notch" else FeatureKind.PROJECTION
            counters[kind] = counters.get(kind, 0) + 1
            o = frame.origin
            mouth3d = Point3(
                o.x + u.x * ch.mouth_mid[0] + v.x * ch.mouth_mid[1],
                o.y + u.y * ch.mouth_mid[0] + v.y * ch.mouth_mid[1],
                o.z + u.z * ch.mouth_mid[0] + v.z * ch.mouth_mid[1],
            )
            feature = Feature(
                id=f"{kind.value}{counters[kind]}",
                kind=kind,
                face_refs=_face_refs(face_idx, partners),
                anchor=mouth3d,
                params={"width_mm": ch.width_mm, "depth_mm": ch.depth_mm},
            )
            results.append((feature, face_idx, mouth3d))
    return results
