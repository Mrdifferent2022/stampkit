"""Rule engine unit tests: builtin library, registry, declarative rules."""

from __future__ import annotations

import pytest

from stampkit.engine.rules_evaluator import RulesEvaluator
from stampkit.model.extraction_result import ExtractionResult
from stampkit.model.features import Feature, FeatureKind
from stampkit.rules.loader import load_builtin_rules, load_yaml_dir
from stampkit.rules.registry import DuplicateRuleError, RuleRegistry
from stampkit.rules.results import Verdict


@pytest.fixture()
def registry() -> RuleRegistry:
    return load_builtin_rules(RuleRegistry())


def _evaluate(registry: RuleRegistry, ctx, features: list[Feature]):
    extraction = ExtractionResult(features=features)
    return RulesEvaluator(registry).evaluate(extraction, ctx)


def test_builtin_library_loads_ten_rules(registry):
    assert len(registry.all()) == 10


def test_notch_width_fix_and_accept(registry, ctx, make_feature):
    narrow = make_feature(FeatureKind.NOTCH, "n1", width_mm=4.0)
    findings = _evaluate(registry, ctx, [narrow])
    fix = [f for f in findings if f.verdict is Verdict.FIX]
    assert len(fix) == 1
    assert fix[0].actual == pytest.approx(4.0)
    assert fix[0].required == pytest.approx(5.0)
    assert fix[0].fix_suggestion

    wide = make_feature(FeatureKind.NOTCH, "n2", width_mm=5.0)
    findings = _evaluate(registry, ctx, [wide])
    assert all(f.verdict is Verdict.ACCEPT for f in findings)


def test_hole_edge_distance_rule(registry, ctx, make_feature):
    close = make_feature(FeatureKind.HOLE, "h1", min_dist_to_edge_mm=2.41, diameter_mm=10.0)
    findings = _evaluate(registry, ctx, [close])
    assert [f.rule_id for f in findings if f.verdict is Verdict.FIX] == ["hole_edge_min_dist"]


def test_pairwise_hole_hole(registry, ctx, make_feature):
    a = make_feature(FeatureKind.HOLE, "h1")
    b = make_feature(FeatureKind.HOLE, "h2")
    # pairwise distance is looked up as "edge_dist_mm@<other_id>"
    a.params["edge_dist_mm@h2"] = 6.0  # 3t = 7.5 -> violation
    findings = _evaluate(registry, ctx, [a, b])
    fix = [f for f in findings if f.verdict is Verdict.FIX]
    assert len(fix) == 1
    assert fix[0].rule_id == "hole_hole_min_dist"


def test_bend_radius_rule_uses_thickness(registry, ctx, make_feature):
    bend = make_feature(FeatureKind.BEND, "b1", radius_mm=1.0, min_dist_to_edge_mm=50.0)
    findings = _evaluate(registry, ctx, [bend])
    fix = {f.rule_id for f in findings if f.verdict is Verdict.FIX}
    assert "bend_min_radius" in fix


def test_ruleset_filtering(registry, ctx, make_feature):
    registry.add_ruleset("notches_only", ["notch_min_width"])
    ctx_strict = type(ctx)(thickness_mm=2.5, material=ctx.material, ruleset="notches_only")
    hole = make_feature(FeatureKind.HOLE, "h1", min_dist_to_edge_mm=0.5)
    findings = _evaluate(registry, ctx_strict, [hole])
    assert findings == []  # hole rules not in this ruleset


def test_duplicate_registration_rejected(registry):
    rule = registry.get("notch_min_width")
    with pytest.raises(DuplicateRuleError):
        registry.register(rule)


def test_custom_yaml_rules_load(registry, tmp_path):
    (tmp_path / "custom.yaml").write_text(
        "- id: hole_min_diameter\n"
        "  feature: hole\n"
        "  metric: diameter_mm\n"
        '  op: ">="\n'
        '  expr: "t"\n',
        encoding="utf-8",
    )
    load_yaml_dir(tmp_path, registry=registry)
    assert registry.get("hole_min_diameter") is not None
