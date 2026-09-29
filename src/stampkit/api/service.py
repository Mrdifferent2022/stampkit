"""StampKitService: the single entry point both manual and AI modes call."""

from __future__ import annotations

import hashlib
from pathlib import Path

from stampkit.api.dto import EvaluateRequest, LocalPathInput, PartInputKind
from stampkit.engine.evaluator import EvaluatorRegistry
from stampkit.engine.pipeline import evaluate as run_evaluation
from stampkit.engine.rules_evaluator import RulesEvaluator
from stampkit.extraction.kernel import GeometryKernel
from stampkit.extraction.pipeline import ExtractionPipeline
from stampkit.model.context import EvaluationContext
from stampkit.model.extraction_result import ExtractionResult
from stampkit.model.material import get_material
from stampkit.report.schema import Report


class StampKitService:
    """Facade: resolves the part input, runs extraction + evaluation.

    The kernel is injected lazily so importing this module never requires a
    CAD kernel; only evaluate() does.
    """

    def __init__(self, kernel: GeometryKernel | None = None) -> None:
        self._kernel = kernel

    def _get_kernel(self) -> GeometryKernel:
        if self._kernel is None:
            from stampkit.backends import get_kernel

            self._kernel = get_kernel()
        return self._kernel

    def evaluate(self, request: EvaluateRequest) -> Report:
        ctx = EvaluationContext(
            thickness_mm=request.thickness_mm,
            material=get_material(request.material),
            ruleset=request.ruleset,
            kernel_settings=request.kernel_settings,
        )
        extraction = self._extract(request)
        registry = EvaluatorRegistry()
        registry.register(RulesEvaluator())
        return run_evaluation(extraction, ctx, registry=registry)

    def evaluate_shape(
        self,
        shape: object,
        *,
        thickness_mm: float,
        material: str,
        ruleset: str = "default",
    ) -> Report:
        """Evaluate an in-memory shape (e.g. a solid in the FreeCAD document).

        The shape stays opaque: nothing kernel-specific is read here, it is
        only forwarded to the extraction pipeline.
        """
        ctx = EvaluationContext(
            thickness_mm=thickness_mm,
            material=get_material(material),
            ruleset=ruleset,
        )
        extraction = ExtractionPipeline(self._get_kernel(), ctx.kernel_settings).run_shape(
            shape, thickness_mm
        )
        registry = EvaluatorRegistry()
        registry.register(RulesEvaluator())
        return run_evaluation(extraction, ctx, registry=registry)

    def _extract(self, request: EvaluateRequest) -> ExtractionResult:
        settings = request.kernel_settings
        if request.part.kind is PartInputKind.LOCAL_PATH:
            assert isinstance(request.part, LocalPathInput)
            path = Path(request.part.path)
            if not path.exists():
                raise FileNotFoundError(f"part file not found: {path}")
            source_hash = hashlib.sha256(path.read_bytes()).hexdigest()
            pipeline = ExtractionPipeline(self._get_kernel(), settings)
            return pipeline.run(str(path), request.thickness_mm, source_hash=source_hash)
        raise NotImplementedError(
            f"part input kind {request.part.kind!r} lands with the bridge/cloud work (Phase 3)"
        )
