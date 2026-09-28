"""Extraction pipeline: shape -> ExtractionResult.

Phase 1 implements hole/slot/bend; Phase 2 adds the full feature set.
"""

from __future__ import annotations

from stampkit.extraction.kernel import GeometryKernel
from stampkit.model.context import KernelSettings
from stampkit.model.extraction_result import ExtractionResult


class ExtractionPipeline:
    def __init__(self, kernel: GeometryKernel, settings: KernelSettings | None = None) -> None:
        self._kernel = kernel
        self._settings = settings or KernelSettings()

    def run(self, step_path: str, source_hash: str = "") -> ExtractionResult:
        raise NotImplementedError("extraction pipeline lands in Phase 1")
