"""Report schema (pydantic). This schema is a stable contract:

- it is the CLI output, the FreeCAD panel's data source, and the tool result
  consumed by AI agents via MCP;
- evolve it additively only: new fields are optional, existing fields never
  change meaning or type. Bump SCHEMA_VERSION on any structural change.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from stampkit.model.context import EvaluationContext
from stampkit.model.extraction_result import ExtractionResult
from stampkit.rules.results import Finding

SCHEMA_VERSION = "1.0"


class FeatureRecord(BaseModel):
    id: str
    kind: str
    params: dict[str, float] = Field(default_factory=dict)
    face_refs: list[str] = Field(default_factory=list)
    #: 3D anchor [x, y, z] for visualization (labels/highlights), if known.
    anchor: list[float] | None = None


class FindingRecord(BaseModel):
    rule_id: str
    feature_id: str
    verdict: str
    actual: float | None = None
    required: float | None = None
    message: str = ""
    fix_suggestion: str = ""
    severity: str = "error"
    evaluator: str = "rules"


class Summary(BaseModel):
    total_features: int = 0
    accepted: int = 0
    to_fix: int = 0

    @classmethod
    def from_findings(cls, findings: list[Finding]) -> Summary:
        fix_features = {f.feature_id for f in findings if f.verdict.value == "fix"}
        accept_features = {f.feature_id for f in findings if f.verdict.value == "accept"}
        return cls(
            total_features=len(fix_features | accept_features),
            accepted=len(accept_features - fix_features),
            to_fix=len(fix_features),
        )


class Report(BaseModel):
    schema_version: str = SCHEMA_VERSION
    stampkit_version: str = ""
    thickness_mm: float
    material: str
    ruleset: str = "default"
    features: list[FeatureRecord] = Field(default_factory=list)
    findings: list[FindingRecord] = Field(default_factory=list)
    summary: Summary = Field(default_factory=Summary)
    warnings: list[str] = Field(default_factory=list)


def build_report(
    *,
    extraction: ExtractionResult,
    ctx: EvaluationContext,
    findings: list[Finding],
    summary: Summary,
) -> Report:
    from stampkit import __version__

    return Report(
        stampkit_version=__version__,
        thickness_mm=ctx.thickness_mm,
        material=ctx.material.name,
        ruleset=ctx.ruleset,
        features=[
            FeatureRecord(
                id=f.id,
                kind=f.kind.value,
                params=dict(f.params),
                face_refs=list(f.face_refs),
                anchor=[f.anchor.x, f.anchor.y, f.anchor.z] if f.anchor else None,
            )
            for f in extraction.features
        ],
        findings=[
            FindingRecord(
                rule_id=x.rule_id,
                feature_id=x.feature_id,
                verdict=x.verdict.value,
                actual=x.actual,
                required=x.required,
                message=x.message,
                fix_suggestion=x.fix_suggestion,
                severity=x.severity,
                evaluator=x.evaluator,
            )
            for x in findings
        ],
        summary=summary,
        warnings=list(extraction.warnings),
    )
