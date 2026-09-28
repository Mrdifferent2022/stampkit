"""Geometric parameter computation.

- hole diameter: longest chord between sampled control points of the wire;
- slot length/width: in-plane extents of the control-point cloud;
- min_dist_to_edge_mm: wire-to-outer-wire distance on the host sheet face;
- pairwise edge_dist_mm@<other_id>: precomputed for same-face pairs and for
  slot-to-bend pairs (used by pairwise rules);
- bend min_dist_to_edge_mm: bend-face to nearest blank-edge face.
"""

from __future__ import annotations

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


def compute_bend_params(
    kernel: GeometryKernel,
    bends: list[tuple[Feature, list[int]]],
    face_by_idx: dict[int, ShapeRef],
    blank_edges: list[tuple[int, ShapeRef]],
    slots: list[PlanarHit],
) -> None:
    for feature, face_indices in bends:
        bend_faces = [face_by_idx[i] for i in face_indices]
        if blank_edges:
            feature.params["min_dist_to_edge_mm"] = min(
                kernel.dist(bf, ef) for bf in bend_faces for _ei, ef in blank_edges
            )
    # slot -> bend distances (parallel-ness refinement lands in Phase 2)
    for slot, wire, _face_idx in slots:
        for bend, face_indices in bends:
            d = min(kernel.dist(wire, face_by_idx[i]) for i in face_indices)
            slot.params[f"edge_dist_mm@{bend.id}"] = d
