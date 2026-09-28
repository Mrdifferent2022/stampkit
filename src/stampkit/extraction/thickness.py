"""Thickness handling via face classification (thin-wall fallback strategy).

Rather than physically removing thickness, the solid's faces are classified:

- **sheet faces**: large planar faces carrying the part's real geometry
  (holes, slots, ...). Both in-plane extents are well above the thickness.
- **blank edges**: thin side-wall faces with one in-plane extent ~= t.
  Edge-distance rules measure against these.

Everything else (non-planar) is handled by the non-planar extractor.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from stampkit.extraction.kernel import GeometryKernel, ShapeRef
from stampkit.model.geometry import BBox, PlaneFrame, Point3, Vector3

#: A planar face whose smallest in-plane extent exceeds factor * t is a sheet face.
_SHEET_FACE_FACTOR = 2.0
#: A planar face whose smallest in-plane extent is within this relative
#: tolerance of t is a blank edge (side wall).
_EDGE_TOL = 0.35


@dataclass(slots=True)
class ClassifiedFaces:
    sheet_faces: list[tuple[int, ShapeRef]] = field(default_factory=list)
    blank_edges: list[tuple[int, ShapeRef]] = field(default_factory=list)
    non_planar: list[tuple[int, ShapeRef]] = field(default_factory=list)
    ignored: list[tuple[int, ShapeRef]] = field(default_factory=list)


def in_plane_extents(corners: list[Point3], frame: PlaneFrame) -> tuple[float, float]:
    """Project bbox corners onto the face plane; return (u_extent, v_extent)."""
    n = frame.normal
    # Build in-plane axes u, v from the normal.
    ref = Vector3(1.0, 0.0, 0.0) if abs(n.x) < 0.9 else Vector3(0.0, 1.0, 0.0)
    u = _cross(n, ref)
    u = _normalize(u)
    v = _cross(n, u)
    o = frame.origin
    us = [(c.x - o.x) * u.x + (c.y - o.y) * u.y + (c.z - o.z) * u.z for c in corners]
    vs = [(c.x - o.x) * v.x + (c.y - o.y) * v.y + (c.z - o.z) * v.z for c in corners]
    return (max(us) - min(us), max(vs) - min(vs))


def _cross(a: Vector3, b: Vector3) -> Vector3:
    return Vector3(a.y * b.z - a.z * b.y, a.z * b.x - a.x * b.z, a.x * b.y - a.y * b.x)


def _normalize(v: Vector3) -> Vector3:
    n = math.sqrt(v.x * v.x + v.y * v.y + v.z * v.z)
    return Vector3(v.x / n, v.y / n, v.z / n)


def bbox_corners(bb: BBox) -> list[Point3]:
    return [
        Point3(x, y, z)
        for x in (bb.xmin, bb.xmax)
        for y in (bb.ymin, bb.ymax)
        for z in (bb.zmin, bb.zmax)
    ]


def classify_faces(
    kernel: GeometryKernel, faces: list[ShapeRef], thickness_mm: float
) -> ClassifiedFaces:
    result = ClassifiedFaces()
    for idx, face in enumerate(faces):
        if not kernel.is_planar(face):
            result.non_planar.append((idx, face))
            continue
        frame = kernel.plane_frame(face)
        u, v = in_plane_extents(bbox_corners(kernel.face_bbox(face)), frame)
        min_extent = min(u, v)
        if min_extent > _SHEET_FACE_FACTOR * thickness_mm:
            result.sheet_faces.append((idx, face))
        elif abs(min_extent - thickness_mm) <= _EDGE_TOL * thickness_mm:
            result.blank_edges.append((idx, face))
        else:
            result.ignored.append((idx, face))
    return result


def dedupe_sheet_faces(
    kernel: GeometryKernel,
    sheet_faces: list[tuple[int, ShapeRef]],
    thickness_mm: float,
    *,
    offset_tol: float = 0.3,
) -> list[tuple[int, ShapeRef]]:
    """Collapse opposing pairs of sheet faces (top/bottom of the same wall).

    Without thickness removal, every punched feature appears as inner wires on
    BOTH sides of the wall. Two faces form a pair when their planes are
    parallel, offset by ~t, and their in-plane footprints overlap.
    """
    frames = [(idx, face, kernel.plane_frame(face)) for idx, face in sheet_faces]
    paired: set[int] = set()
    keep: list[tuple[int, ShapeRef]] = []
    for i, (idx_a, face_a, fa) in enumerate(frames):
        if idx_a in paired:
            continue
        keep.append((idx_a, face_a))
        for idx_b, face_b, fb in frames[i + 1 :]:
            if idx_b in paired:
                continue
            if _is_opposing_pair(kernel, face_a, fa, face_b, fb, thickness_mm, offset_tol):
                paired.add(idx_b)
    return keep


def _is_opposing_pair(
    kernel: GeometryKernel,
    face_a: ShapeRef,
    fa: PlaneFrame,
    face_b: ShapeRef,
    fb: PlaneFrame,
    t: float,
    offset_tol: float,
) -> bool:
    na, nb = fa.normal, fb.normal
    dot = abs(na.x * nb.x + na.y * nb.y + na.z * nb.z)
    len_a = math.sqrt(na.x**2 + na.y**2 + na.z**2)
    len_b = math.sqrt(nb.x**2 + nb.y**2 + nb.z**2)
    if len_a == 0 or len_b == 0 or abs(dot / (len_a * len_b) - 1.0) > 0.02:
        return False  # not parallel
    # Perpendicular offset between the two planes.
    dx, dy, dz = fb.origin.x - fa.origin.x, fb.origin.y - fa.origin.y, fb.origin.z - fa.origin.z
    unit = Vector3(na.x / len_a, na.y / len_a, na.z / len_a)
    offset = abs(dx * unit.x + dy * unit.y + dz * unit.z)
    if abs(offset - t) > offset_tol * t:
        return False
    # In-plane footprint overlap on both axes of face A's frame.
    corners_b = bbox_corners(kernel.face_bbox(face_b))
    for axis_u in _frame_axes(fa):
        proj_a = _project(bbox_corners(kernel.face_bbox(face_a)), fa.origin, axis_u)
        proj_b = _project(corners_b, fa.origin, axis_u)
        overlap = min(max(proj_a), max(proj_b)) - max(min(proj_a), min(proj_b))
        if overlap <= 0:
            return False
    return True


def _frame_axes(frame: PlaneFrame) -> tuple[Vector3, Vector3]:
    n = frame.normal
    ref = Vector3(1.0, 0.0, 0.0) if abs(n.x) < 0.9 else Vector3(0.0, 1.0, 0.0)
    u = _normalize(_cross(n, ref))
    return u, _cross(n, u)


def _project(points: list[Point3], origin: Point3, axis: Vector3) -> list[float]:
    return [(p.x - origin.x) * axis.x + (p.y - origin.y) * axis.y + (p.z - origin.z) * axis.z for p in points]
