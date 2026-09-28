"""Compile declarative YAML rule descriptors into Rule objects."""

from __future__ import annotations

from typing import Any

from stampkit.model.context import EvaluationContext
from stampkit.model.features import Feature, FeatureKind
from stampkit.rules.base import Rule, RuleScope, Severity
from stampkit.rules.expressions import evaluate_expr
from stampkit.rules.results import Finding, Verdict
from stampkit.rules.world import FeatureWorld

_OPS = {
    ">=": lambda a, b: a >= b,
    "<=": lambda a, b: a <= b,
    ">": lambda a, b: a > b,
    "<": lambda a, b: a < b,
    "==": lambda a, b: abs(a - b) < 1e-9,
}


class DeclarativeRuleError(ValueError):
    pass


def _variables(ctx: EvaluationContext, feature: Feature) -> dict[str, float]:
    v: dict[str, float] = {
        "t": ctx.thickness_mm,
        "R": feature.param("radius_mm") or 0.0,
    }
    for key, val in feature.params.items():
        v.setdefault(key, val)
    return v


class _MetricRule(Rule):
    """A rule compiled from a YAML descriptor."""

    def __init__(self, spec: dict[str, Any]) -> None:
        try:
            self.id = str(spec["id"])
            self._metric = str(spec["metric"])
            self._op = str(spec["op"])
            self._expr = str(spec["expr"])
            self.feature_kinds = (FeatureKind(str(spec["feature"])),)
        except KeyError as e:
            raise DeclarativeRuleError(f"missing key {e} in rule spec {spec!r}") from e
        if self._op not in _OPS:
            raise DeclarativeRuleError(f"unsupported op {self._op!r} in {self.id!r}")
        self.scope = RuleScope(str(spec.get("scope", "single")))
        other = spec.get("other")
        self.other_kind = FeatureKind(str(other)) if other else None
        if self.scope is RuleScope.PAIRWISE and self.other_kind is None:
            raise DeclarativeRuleError(f"pairwise rule {self.id!r} needs 'other'")
        self.severity = Severity(str(spec.get("severity", "error")))
        self.description = str(spec.get("description", ""))
        self._fix_tpl = str(spec.get("fix", ""))

    def check(
        self,
        feature: Feature,
        ctx: EvaluationContext,
        world: FeatureWorld,
        other: Feature | None = None,
    ) -> list[Finding]:
        actual = world.metric_between(feature, other, self._metric) if other else feature.param(self._metric)
        if actual is None:
            return []  # metric not measurable for this feature: rule not applicable
        variables = _variables(ctx, feature)
        if other is not None and other.param("radius_mm") is not None:
            variables["R"] = other.param("radius_mm") or 0.0
        required = evaluate_expr(self._expr, variables)
        ok = _OPS[self._op](actual, required)
        if ok:
            return [
                Finding(
                    rule_id=self.id,
                    feature_id=feature.id,
                    verdict=Verdict.ACCEPT,
                    actual=actual,
                    required=required,
                    message=self.description,
                )
            ]
        fix = self._fix_tpl.format(actual=actual, required=required) if self._fix_tpl else ""
        return [
            Finding(
                rule_id=self.id,
                feature_id=feature.id,
                verdict=Verdict.FIX,
                actual=actual,
                required=required,
                message=self.description or f"{self._metric} {self._op} {self._expr}",
                fix_suggestion=fix,
                severity=self.severity.value,
            )
        ]


def compile_rule(spec: dict[str, Any]) -> Rule:
    """Compile one YAML rule descriptor (already parsed to a dict)."""
    return _MetricRule(spec)
