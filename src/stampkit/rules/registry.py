"""Rule registry: the single funnel for all rule registration."""

from __future__ import annotations

from collections.abc import Callable, Iterable

from stampkit.model.features import FeatureKind
from stampkit.rules.base import Rule


class DuplicateRuleError(ValueError):
    pass


class UnknownRuleError(KeyError):
    pass


class RuleRegistry:
    """Ordered registry of rules with enable/disable, tags and rulesets."""

    def __init__(self) -> None:
        self._rules: dict[str, Rule] = {}
        self._tags: dict[str, set[str]] = {}
        self._rulesets: dict[str, set[str]] = {"default": set()}

    def register(
        self,
        rule: Rule,
        *,
        tags: Iterable[str] = (),
        rulesets: Iterable[str] = ("default",),
    ) -> Rule:
        if not getattr(rule, "id", None):
            raise ValueError(f"rule {type(rule).__name__} has no id")
        if rule.id in self._rules:
            raise DuplicateRuleError(f"rule id {rule.id!r} already registered")
        self._rules[rule.id] = rule
        self._tags.setdefault(rule.id, set()).update(tags)
        for name in rulesets:
            self._rulesets.setdefault(name, set()).add(rule.id)
        return rule

    def unregister(self, rule_id: str) -> None:
        if rule_id not in self._rules:
            raise UnknownRuleError(rule_id)
        del self._rules[rule_id]
        self._tags.pop(rule_id, None)
        for ids in self._rulesets.values():
            ids.discard(rule_id)

    def get(self, rule_id: str) -> Rule:
        try:
            return self._rules[rule_id]
        except KeyError:
            raise UnknownRuleError(rule_id) from None

    def all(self) -> list[Rule]:
        """All rules in deterministic (id-sorted) order."""
        return [self._rules[k] for k in sorted(self._rules)]

    def for_kind(self, kind: FeatureKind, *, ruleset: str = "default") -> list[Rule]:
        ids = self._rulesets.get(ruleset)
        if ids is None:
            raise UnknownRuleError(f"ruleset {ruleset!r}")
        return [r for r in self.all() if r.id in ids and kind in r.feature_kinds]

    def with_tags(self, *tags: str) -> list[Rule]:
        wanted = set(tags)
        return [r for r in self.all() if self._tags.get(r.id, set()) & wanted]

    def add_ruleset(self, name: str, rule_ids: Iterable[str]) -> None:
        ids = set(rule_ids)
        unknown = ids - set(self._rules)
        if unknown:
            raise UnknownRuleError(f"unknown rule ids: {sorted(unknown)}")
        self._rulesets[name] = ids

    def rulesets(self) -> list[str]:
        return sorted(self._rulesets)


#: Process-wide default registry; library and loaders register into it.
default_registry = RuleRegistry()


def register_rule(
    cls_or_rule: type[Rule] | Rule | None = None,
    *,
    tags: Iterable[str] = (),
    rulesets: Iterable[str] = ("default",),
    registry: RuleRegistry | None = None,
) -> Callable[..., object] | Rule:
    """Decorator (or direct call) registering a Rule into a registry."""

    reg = registry or default_registry

    def wrap(obj: type[Rule] | Rule) -> type[Rule] | Rule:
        instance = obj() if isinstance(obj, type) else obj
        reg.register(instance, tags=tags, rulesets=rulesets)
        return obj

    if cls_or_rule is not None:
        return wrap(cls_or_rule)
    return wrap
