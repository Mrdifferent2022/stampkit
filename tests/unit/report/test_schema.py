"""Report schema round-trip tests."""

from __future__ import annotations

from stampkit.model.context import EvaluationContext
from stampkit.model.extraction_result import ExtractionResult
from stampkit.model.features import Feature, FeatureKind
from stampkit.model.material import get_material
from stampkit.report.json_io import from_json, to_json
from stampkit.report.schema import Summary, build_report
from stampkit.rules.results import Finding, Verdict


def _sample_report():
    ctx = EvaluationContext(thickness_mm=2.5, material=get_material("steel"))
    extraction = ExtractionResult(
        features=[Feature(id="n1", kind=FeatureKind.NOTCH, params={"width_mm": 4.0})]
    )
    findings = [
        Finding(
            rule_id="notch_min_width",
            feature_id="n1",
            verdict=Verdict.FIX,
            actual=4.0,
            required=5.0,
            fix_suggestion="widen",
        )
    ]
    return build_report(
        extraction=extraction, ctx=ctx, findings=findings, summary=Summary.from_findings(findings)
    )


def test_json_round_trip():
    report = _sample_report()
    clone = from_json(to_json(report))
    assert clone == report
    assert clone.summary.to_fix == 1


def test_schema_version_recorded():
    assert _sample_report().schema_version == "1.0"
