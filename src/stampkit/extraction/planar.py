"""Planar-face feature extraction: holes and slots from inner wires.

Inner wires of sheet faces are hole/slot candidates; the roundness ratio
(area / centroid-to-outline-distance^2 vs pi) discriminates holes from slots.
Notches/projections/relief-cuts (outline features) land in Phase 2.
"""

from __future__ import annotations

from stampkit.extraction.kernel import GeometryKernel, ShapeRef
from stampkit.extraction.roundness_test import is_round
from stampkit.model.features import Feature, FeatureKind

#: (feature, host wire, host sheet-face index) — handles stay inside extraction.
PlanarHit = tuple[Feature, ShapeRef, int]


def extract_planar_features(
    kernel: GeometryKernel, sheet_faces: list[tuple[int, ShapeRef]]
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
                face_refs=(f"face:{face_idx}",),
                params={"area_mm2": area},
            )
            hits.append((feature, wire, face_idx))
    return hits
