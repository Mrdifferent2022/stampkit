"""Non-planar feature extraction.

Phase 1: bends. A folded sheet produces two coaxial cylindrical faces per bend
(inner radius R and outer radius R + t); coaxial pairs are merged into a
single bend feature whose radius is the inner radius.
Phase 2: sewing into open shells and classifying emboss/drawing/extruded-hole.
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
    kernel: GeometryKernel, non_planar: list[tuple[int, ShapeRef]], thickness_mm: float
) -> tuple[list[tuple[Feature, list[int]]], list[str]]:
    """Identify bends among non-planar faces.

    Cylindrical faces are filtered first: through-hole walls (closed circular
    boundary) and slot walls (axial span ~= t, i.e. straight-through cuts) are
    not bends. Remaining cylinders are grouped by coaxial axes so the inner
    and outer walls of one fold merge into a single bend (inner radius kept).

    Returns (list of (bend feature, source face indices), warnings).
    """
    cylinders: list[tuple[int, ShapeRef, float, tuple[Point3, Vector3]]] = []
    warnings: list[str] = []
    for face_idx, face in non_planar:
        radius = kernel.cylinder_radius(face)
        axis = kernel.cylinder_axis(face)
        if radius is None or axis is None:
            warnings.append(
                f"face:{face_idx}: non-planar, non-cylindrical face not classified (Phase 2)"
            )
            continue
        if kernel.has_closed_circle_edge(face):
            continue  # through-hole wall
        span = kernel.cylinder_axial_span(face)
        if span is not None and abs(span - thickness_mm) <= 0.35 * thickness_mm:
            continue  # straight-through cut wall (slot/oblong), not a fold
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
    return features, warnings
