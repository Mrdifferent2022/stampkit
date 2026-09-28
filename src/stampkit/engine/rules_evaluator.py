"""Rule-engine evaluator: runs the rule registry over shearing-type features."""

from __future__ import annotations

from stampkit.engine.evaluator import Evaluator
from stampkit.model.context import EvaluationContext
from stampkit.model.extraction_result import ExtractionResult
from stampkit.model.features import RULE_EVALUATED_KINDS, FeatureKind
from stampkit.rules.base import RuleScope
from stampkit.rules.loader import load_builtin_rules
from stampkit.rules.registry import RuleRegistry
from stampkit.rules.results import Finding
from stampkit.rules.world import FeatureWorld


class RulesEvaluator(Evaluator):
    name = "rules"

    def __init__(self, registry: RuleRegistry | None = None) -> None:
        self._registry = registry or load_builtin_rules()

    def kinds(self) -> frozenset[FeatureKind]:
        return RULE_EVALUATED_KINDS

    def evaluate(self, extraction: ExtractionResult, ctx: EvaluationContext) -> list[Finding]:
        world = FeatureWorld(extraction.features)
        findings: list[Finding] = []
        kinds_present = {f.kind for f in extraction.features}
        for kind in sorted(kinds_present & self.kinds(), key=str):
            for rule in self._registry.for_kind(kind, ruleset=ctx.ruleset):
                if rule.scope is RuleScope.PAIRWISE:
                    for a, b in world.pairs(kind, rule.other_kind):
                        findings.extend(rule.check(a, ctx, world, b))
                else:
                    for feature in world.by_kind(kind):
                        findings.extend(rule.check(feature, ctx, world))
        return findings
