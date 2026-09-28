"""Extraction pipeline: shape -> ExtractionResult.

Phase 1: hole/slot (planar inner wires + roundness test) and bend (coaxial
cylinder merging). Phase 2 adds outline features and shell classification.
"""

from __future__ import annotations

from stampkit.extraction import nonplanar, params, planar, thickness
from stampkit.extraction.kernel import GeometryKernel
from stampkit.model.context import KernelSettings
from stampkit.model.extraction_result import ExtractionResult
from stampkit.model.features import FeatureKind


class ExtractionPipeline:
    def __init__(self, kernel: GeometryKernel, settings: KernelSettings | None = None) -> None:
        self._kernel = kernel
        self._settings = settings or KernelSettings()

    def run(self, step_path: str, thickness_mm: float, source_hash: str = "") -> ExtractionResult:
        kernel = self._kernel
        shape = kernel.import_step(step_path)
        all_faces = kernel.faces(shape)
        face_by_idx = dict(enumerate(all_faces))

        classified = thickness.classify_faces(kernel, all_faces, thickness_mm)
        sheet_faces = thickness.dedupe_sheet_faces(kernel, classified.sheet_faces, thickness_mm)

        hits = planar.extract_planar_features(kernel, sheet_faces)
        bends, warnings = nonplanar.extract_bends(kernel, classified.non_planar, thickness_mm)

        params.compute_planar_params(kernel, hits, face_by_idx, self._settings)
        slots = [h for h in hits if h[0].kind is FeatureKind.SLOT]
        params.compute_bend_params(kernel, bends, face_by_idx, classified.blank_edges, slots)

        if not classified.sheet_faces:
            warnings.append("no sheet faces detected; check the thickness value")

        features = [h[0] for h in hits] + [b[0] for b in bends]
        return ExtractionResult(features=features, warnings=warnings, source_hash=source_hash)
