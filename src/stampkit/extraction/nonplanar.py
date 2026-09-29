"""Non-planar feature extraction.

- Bends: coaxial cylinder pairs (inner/outer walls of one fold), excluding
  through-hole walls (closed circular boundary) and straight-through cut
  walls (axial span ~= t).
- Shell classification (Phase 2): remaining non-planar faces are grouped by
  edge connectivity and classified as emboss (one plane, one boundary loop),
  extruded hole (coaxial tube walls), or drawing (shell spans 2+ planes).
  These are geometric heuristics to be validated against real parts.
"""

from __future__ import annotations

import math

from stampkit.extraction.kernel import GeometryKernel, ShapeRef
from stampkit.model.features import Feature, FeatureKind
from stampkit.model.geometry import Point3, Vector3

_AXIS_ANGLE_TOL = 0.02  # ~1 degree, as max |dot| deviation from 1
_AXIS_DIST_TOL = 0.5  # mm between axis lines


def _axis_distance(p1: Point3, d1: Vector3, p2: Point3, d2: Vector3) -> float:
    """Distance between two parallel lines (p1,d1) and (p2,d2)."""
    wx, wy, wz = p2.x - p1.x, p2.y - p1.y, p2.z - p1.z
    # component of (p2-p1) perpendicular to d1
    proj = wx * d1.x + wy * d1.y + wz * d1.z
    px, py, pz = wx - proj * d1.x, wy - proj * d1.y, wz - proj * d1.z
    return math.sqrt(px * px + py * py + pz * pz)


def _coaxial(a1: tuple[Point3, Vector3], a2: tuple[Point3, Vector3]) -> bool:
    p1, d1 = a1
    p2, d2 = a2
    dot = abs(d1.x * d2.x + d1.y * d2.y + d1.z * d2.z)
    n1 = (d1.x**2 + d1.y**2 + d1.z**2) ** 0.5
    n2 = (d2.x**2 + d2.y**2 + d2.z**2) ** 0.5
    if n1 == 0 or n2 == 0:
        return False
    if abs(dot / (n1 * n2) - 1.0) > _AXIS_ANGLE_TOL:
        return False
    return _axis_distance(p1, d1, p2, d2) <= _AXIS_DIST_TOL


def extract_bends(
    kernel: GeometryKernel,
    non_planar: list[tuple[int, ShapeRef]],
    thickness_mm: float,
    sheet_faces: list[tuple[int, ShapeRef]],
) -> tuple[list[tuple[Feature, list[int]]], list[tuple[int, ShapeRef]], list[str]]:
    """Identify bends among non-planar faces.

    A bend cylinder must connect two sheet faces (its axial boundary edges are
    shared with the large planar walls). Cylinders failing this (e.g. fillets
    around a drawn pocket) are passed on to shell classification.

    Returns (bends as (feature, face indices), leftover faces for shell
    classification, warnings).
    """
    cylinders: list[tuple[int, ShapeRef, float, tuple[Point3, Vector3]]] = []
    leftover: list[tuple[int, ShapeRef]] = []
    warnings: list[str] = []
    for face_idx, face in non_planar:
        radius = kernel.cylinder_radius(face)
        axis = kernel.cylinder_axis(face)
        if radius is None or axis is None:
            leftover.append((face_idx, face))
            continue
        span = kernel.cylinder_axial_span(face)
        if kernel.has_closed_circle_edge(face):
            if span is not None and abs(span - thickness_mm) <= 0.35 * thickness_mm:
                continue  # through-hole wall
            leftover.append((face_idx, face))  # tube wall (flanged hole, boss)
            continue
        if span is not None and abs(span - thickness_mm) <= 0.35 * thickness_mm:
            continue  # straight-through cut wall (slot/oblong), not a fold
        sheet_touches = sum(
            1 for _si, sface in sheet_faces if kernel.shared_edges(face, sface)
        )
        if sheet_touches < 2:
            leftover.append((face_idx, face))  # rim fillet etc., not a fold
            continue
        cylinders.append((face_idx, face, radius, axis))

    # Group coaxial cylinders into bends (inner + outer wall of one fold).
    groups: list[list[tuple[int, ShapeRef, float, tuple[Point3, Vector3]]]] = []
    for item in cylinders:
        for group in groups:
            if _coaxial(item[3], group[0][3]):
                group.append(item)
                break
        else:
            groups.append([item])

    features: list[tuple[Feature, list[int]]] = []
    for i, group in enumerate(groups, start=1):
        inner_radius = min(g[2] for g in group)
        face_indices = sorted(g[0] for g in group)
        features.append(
            (
                Feature(
                    id=f"bend{i}",
                    kind=FeatureKind.BEND,
                    face_refs=tuple(f"face:{i}" for i in face_indices),
                    params={"radius_mm": inner_radius},
                ),
                face_indices,
            )
        )
    return features, leftover, warnings


def classify_shells(
    kernel: GeometryKernel,
    leftover: list[tuple[int, ShapeRef]],
    planar_faces: list[tuple[int, ShapeRef]],
) -> tuple[list[Feature], list[str]]:
    """Classify leftover non-planar faces as emboss/extruded-hole/drawing.

    Heuristics (to be validated on real parts):
    - shells containing coaxial tube walls (closed-circle cylinders) merge
      into a single extruded hole;
    - a shell sharing edges with 2+ planar faces is a drawing;
    - a shell sharing edges with exactly 1 planar face and bounded by one
      boundary loop is an emboss.
    """
    features: list[Feature] = []
    warnings: list[str] = []
    if not leftover:
        return features, warnings

    faces = [f for _i, f in leftover]
    groups = kernel.group_connected_faces(faces)
    counters: dict[FeatureKind, int] = {}

    def emit(kind: FeatureKind, face_indices: list[int], params: dict[str, float]) -> None:
        counters[kind] = counters.get(kind, 0) + 1
        features.append(
            Feature(
                id=f"{kind.value}{counters[kind]}",
                kind=kind,
                face_refs=tuple(f"face:{i}" for i in sorted(face_indices)),
                params=params,
            )
        )

    # Planar adjacency: how many distinct planar faces share an edge with the shell.
    def planar_touch_count(group_faces: list[ShapeRef]) -> int:
        count = 0
        for _pi, pface in planar_faces:
            for gface in group_faces:
                if kernel.shared_edges(gface, pface):
                    count += 1
                    break
        return count

    def tube_axes(group_faces: list[ShapeRef]) -> list[tuple[Point3, Vector3]]:
        axes = []
        for gface in group_faces:
            if kernel.has_closed_circle_edge(gface):
                axis = kernel.cylinder_axis(gface)
                if axis is not None:
                    axes.append(axis)
        return axes

    extruded_groups: list[list[int]] = []
    pending: list[tuple[list[int], list[ShapeRef]]] = []
    for group in groups:
        group_faces = [faces[i] for i in group]
        if tube_axes(group_faces):
            extruded_groups.append(group)
        else:
            pending.append((group, group_faces))

    # Merge shells whose tube walls are coaxial (inner+outer of one collar).
    merged: list[list[int]] = []
    for group in extruded_groups:
        axes = tube_axes([faces[i] for i in group])
        for other in merged:
            other_axes = tube_axes([faces[i] for i in other])
            if any(_coaxial(a, b) for a in axes for b in other_axes):
                other.extend(group)
                break
        else:
            merged.append(list(group))

    for group in merged:
        idxs = [leftover[i][0] for i in group]
        radii = [
            kernel.cylinder_radius(faces[i]) or 0.0 for i in group
        ]
        emit(FeatureKind.EXTRUDED_HOLE, idxs, {"radius_mm": min(radii) if radii else 0.0})

    for group, group_faces in pending:
        idxs = [leftover[i][0] for i in group]
        touches = planar_touch_count(group_faces)
        loops = kernel.boundary_loop_count(group_faces)
        if touches >= 2:
            emit(FeatureKind.DRAWING, idxs, {})
        elif touches == 1 and loops == 1:
            emit(FeatureKind.EMBOSS, idxs, {})
        else:
            warnings.append(
                f"faces {idxs}: non-planar shell unclassified "
                f"(touches {touches} planes, {loops} boundary loops)"
            )
    return features, warnings
