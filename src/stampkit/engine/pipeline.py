"""The single evaluation pipeline: ExtractionResult + Context -> Report."""

from __future__ import annotations

from stampkit.engine.evaluator import EvaluatorRegistry, default_evaluators
from stampkit.model.context import EvaluationContext
from stampkit.model.extraction_result import ExtractionResult
from stampkit.model.features import FeatureKind
from stampkit.report.schema import Report, Summary, build_report


def _ensure_default_evaluators(registry: EvaluatorRegistry) -> EvaluatorRegistry:
    from stampkit.engine.rules_evaluator import RulesEvaluator

    if not registry.evaluators_for(iter(_all_kinds())):
        registry.register(RulesEvaluator())
    return registry


def _all_kinds() -> list[FeatureKind]:
    return list(FeatureKind)


def evaluate(
    extraction: ExtractionResult,
    ctx: EvaluationContext,
    *,
    registry: EvaluatorRegistry | None = None,
) -> Report:
    """Run all registered evaluators and assemble the report."""
    reg = _ensure_default_evaluators(registry or default_evaluators)
    findings = []
    kinds = {f.kind for f in extraction.features}
    for evaluator in reg.evaluators_for(kinds):
        findings.extend(evaluator.evaluate(extraction, ctx))
    summary = Summary.from_findings(findings)
    return build_report(extraction=extraction, ctx=ctx, findings=findings, summary=summary)
