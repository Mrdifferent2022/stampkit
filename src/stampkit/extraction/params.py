"""Geometric parameter computation.

- hole diameter: longest chord between sampled control points of the wire;
- slot length/width: in-plane extents of the control-point cloud;
- min_dist_to_edge_mm: wire-to-outer-wire distance on the host sheet face;
- pairwise edge_dist_mm@<other_id>: precomputed for same-face pairs and for
  slot-to-bend pairs (used by pairwise rules);
- bend min_dist_to_edge_mm: shortest flange length (sheet-face extent
  perpendicular to the tangent line).
"""

from __future__ import annotations

import math

from stampkit.extraction.kernel import GeometryKernel, ShapeRef
from stampkit.extraction.planar import PlanarHit
from stampkit.extraction.thickness import in_plane_extents
from stampkit.model.context import KernelSettings
from stampkit.model.features import Feature, FeatureKind
from stampkit.model.geometry import Point3


def _max_chord(points: list[Point3]) -> float:
    best = 0.0
    for i, a in enumerate(points):
        for b in points[i + 1 :]:
            d = a.distance_to(b)
            if d > best:
                best = d
    return best


def compute_planar_params(
    kernel: GeometryKernel,
    hits: list[PlanarHit],
    face_by_idx: dict[int, ShapeRef],
    settings: KernelSettings,
) -> None:
    # Per-feature params.
    for feature, wire, face_idx in hits:
        points = kernel.control_points(wire, settings.control_point_samples)
        if feature.kind is FeatureKind.HOLE:
            feature.params["diameter_mm"] = _max_chord(points)
        else:
            frame = kernel.plane_frame(face_by_idx[face_idx])
            u, v = in_plane_extents(points, frame)
            feature.params["length_mm"] = max(u, v)
            feature.params["width_mm"] = min(u, v)
        outer, _ = kernel.wires(face_by_idx[face_idx])
        feature.params["min_dist_to_edge_mm"] = kernel.dist(wire, outer)

    # Pairwise distances within the same sheet face.
    for i, (fa, wa, face_a) in enumerate(hits):
        for fb, wb, face_b in hits[i + 1 :]:
            if face_a != face_b:
                continue
            d = kernel.dist(wa, wb)
            fa.params[f"edge_dist_mm@{fb.id}"] = d
            fb.params[f"edge_dist_mm@{fa.id}"] = d


def _is_straight(kernel: GeometryKernel, edge: ShapeRef) -> bool:
    p1, p2 = kernel.edge_endpoints(edge)
    chord = p1.distance_to(p2)
    return abs(kernel.edge_length(edge) - chord) <= max(1e-4, 1e-4 * chord)


def _dist_to_line(p: Point3, a: Point3, b: Point3) -> float:
    """Distance from point p to the infinite line through a and b."""
    dx, dy, dz = b.x - a.x, b.y - a.y, b.z - a.z
    norm = math.sqrt(dx * dx + dy * dy + dz * dz)
    if norm < 1e-12:
        return p.distance_to(a)
    wx, wy, wz = p.x - a.x, p.y - a.y, p.z - a.z
    cx, cy, cz = wy * dz - wz * dy, wz * dx - wx * dz, wx * dy - wy * dx
    return math.sqrt(cx * cx + cy * cy + cz * cz) / norm


def compute_bend_params(
    kernel: GeometryKernel,
    bends: list[tuple[Feature, list[int]]],
    face_by_idx: dict[int, ShapeRef],
    sheet_faces: list[tuple[int, ShapeRef]],
    slots: list[PlanarHit],
    settings: KernelSettings,
) -> None:
    for feature, face_indices in bends:
        bend_faces = [face_by_idx[i] for i in face_indices]
        # min_dist_to_edge_mm = shortest flange length: for each sheet face
        # sharing a straight tangent edge with the bend, the extent of that
        # face perpendicular to the tangent line. Measuring to blank-edge
        # faces instead would unfairly flag legitimate relief-cuts.
        flange_lengths: list[float] = []
        for _si, sface in sheet_faces:
            tangents = [
                e
                for bf in bend_faces
                for e in kernel.shared_edges(sface, bf)
                if _is_straight(kernel, e)
            ]
            if not tangents:
                continue
            p1, p2 = kernel.edge_endpoints(max(tangents, key=kernel.edge_length))
            outer, _ = kernel.wires(sface)
            pts = kernel.control_points(outer, settings.control_point_samples)
            flange_lengths.append(max(_dist_to_line(p, p1, p2) for p in pts))
        if flange_lengths:
            feature.params["min_dist_to_edge_mm"] = min(flange_lengths)
    # slot -> bend distances
    for slot, wire, _face_idx in slots:
        for bend, face_indices in bends:
            d = min(kernel.dist(wire, face_by_idx[i]) for i in face_indices)
            slot.params[f"edge_dist_mm@{bend.id}"] = d
