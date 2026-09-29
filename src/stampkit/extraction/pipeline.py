"""Extraction pipeline: shape -> ExtractionResult.

Phase 1: hole/slot (planar inner wires + roundness test), bend (coaxial
cylinder merging). Phase 2: notches/projections (outline channel detection),
relief-cuts (notches reclassified near bend tangent edges), and non-planar
shell classification (emboss / extruded hole / drawing).
"""

from __future__ import annotations

import math

from stampkit.extraction import nonplanar, params, planar, thickness
from stampkit.extraction.kernel import GeometryKernel
from stampkit.model.context import KernelSettings
from stampkit.model.extraction_result import ExtractionResult
from stampkit.model.features import Feature, FeatureKind
from stampkit.model.geometry import Point3


def _dist_to_line(p: Point3, a: Point3, b: Point3) -> float:
    """Distance from point p to the infinite line through a and b."""
    dx, dy, dz = b.x - a.x, b.y - a.y, b.z - a.z
    norm = math.sqrt(dx * dx + dy * dy + dz * dz)
    if norm < 1e-12:
        return p.distance_to(a)
    wx, wy, wz = p.x - a.x, p.y - a.y, p.z - a.z
    cx, cy, cz = wy * dz - wz * dy, wz * dx - wx * dz, wx * dy - wy * dx
    return math.sqrt(cx * cx + cy * cy + cz * cz) / norm


class ExtractionPipeline:
    def __init__(self, kernel: GeometryKernel, settings: KernelSettings | None = None) -> None:
        self._kernel = kernel
        self._settings = settings or KernelSettings()

    def run(self, step_path: str, thickness_mm: float, source_hash: str = "") -> ExtractionResult:
        shape = self._kernel.import_step(step_path)
        return self.run_shape(shape, thickness_mm, source_hash=source_hash)

    def run_shape(
        self, shape: object, thickness_mm: float, source_hash: str = ""
    ) -> ExtractionResult:
        kernel = self._kernel
        settings = self._settings
        all_faces = kernel.faces(shape)
        face_by_idx = dict(enumerate(all_faces))

        classified = thickness.classify_faces(kernel, all_faces, thickness_mm)
        sheet_reps = thickness.dedupe_sheet_faces(kernel, classified.sheet_faces, thickness_mm)
        rep_faces = [(i, f) for i, f, _ps in sheet_reps]
        partners = {i: ps for i, _f, ps in sheet_reps if ps}
        paired_faces = [(i, f) for i, f, ps in sheet_reps if ps]
        outline_faces = paired_faces or rep_faces

        hits = planar.extract_planar_features(kernel, rep_faces, partners)
        bends, leftover, warnings = nonplanar.extract_bends(
            kernel, classified.non_planar, thickness_mm, classified.sheet_faces
        )
        shell_features, shell_warnings = nonplanar.classify_shells(
            kernel, leftover, classified.all_planar()
        )
        warnings.extend(shell_warnings)

        outline_hits = planar.extract_outline_features(kernel, outline_faces, settings, partners)
        outline_features = [
            self._reclassify_relief_cut(feature, face_idx, mouth, face_by_idx, bends)
            for feature, face_idx, mouth in outline_hits
        ]

        params.compute_planar_params(kernel, hits, face_by_idx, settings)
        slots = [h for h in hits if h[0].kind is FeatureKind.SLOT]
        params.compute_bend_params(
            kernel, bends, face_by_idx, classified.sheet_faces, slots, settings
        )

        if not classified.sheet_faces:
            warnings.append("no sheet faces detected; check the thickness value")

        features = (
            [h[0] for h in hits]
            + outline_features
            + [b[0] for b in bends]
            + shell_features
        )
        return ExtractionResult(features=features, warnings=warnings, source_hash=source_hash)

    def _reclassify_relief_cut(
        self,
        feature: Feature,
        face_idx: int,
        mouth: Point3,
        face_by_idx: dict[int, object],
        bends: list[tuple[Feature, list[int]]],
    ) -> Feature:
        """A notch whose mouth touches a bend tangent edge is a relief-cut."""
        if feature.kind is not FeatureKind.NOTCH:
            return feature
        kernel = self._kernel
        host = face_by_idx[face_idx]
        for bend, bend_face_indices in bends:
            for bfi in bend_face_indices:
                for edge in kernel.shared_edges(host, face_by_idx[bfi]):
                    # the tangent edge may itself be trimmed by the relief cut,
                    # so measure against the infinite tangent LINE instead;
                    # the cut qualifies when its near corner touches the bend
                    p1, p2 = kernel.edge_endpoints(edge)
                    half_width = feature.params.get("width_mm", 0.0) / 2.0
                    prox = max(0.0, _dist_to_line(mouth, p1, p2) - half_width)
                    if prox <= self._settings.relief_cut_tol_mm:
                        return Feature(
                            id=feature.id.replace("notch", "relief_cut", 1),
                            kind=FeatureKind.RELIEF_CUT,
                            face_refs=feature.face_refs,
                            outline=feature.outline,
                            plane=feature.plane,
                            anchor=feature.anchor,
                            params={
                                "width_mm": feature.params.get("width_mm", 0.0),
                                "length_mm": feature.params.get("depth_mm", 0.0),
                                # rules need the adjacent bend's radius
                                "radius_mm": bend.params.get("radius_mm", 0.0),
                            },
                        )
        return feature
