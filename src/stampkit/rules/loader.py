"""Rule loading: builtin library, YAML directories, entry points."""

from __future__ import annotations

from importlib.metadata import entry_points
from pathlib import Path

import yaml

from stampkit.rules.declarative import compile_rule
from stampkit.rules.registry import RuleRegistry, default_registry

ENTRY_POINT_GROUP = "stampkit.rules"


def load_builtin_rules(registry: RuleRegistry | None = None) -> RuleRegistry:
    """Register the builtin rule library (code + bundled YAML)."""
    reg = registry or default_registry
    from stampkit.rules import library  # noqa: F401  (import side effect: registers rules)

    lib_yaml = Path(library.__file__).with_name("library.yaml")
    if lib_yaml.exists():
        load_yaml_dir(lib_yaml.parent, registry=reg, filenames={lib_yaml.name})
    return reg


def load_yaml_dir(
    path: str | Path,
    *,
    registry: RuleRegistry | None = None,
    filenames: set[str] | None = None,
) -> RuleRegistry:
    """Load all YAML rule descriptors from a directory into the registry."""
    reg = registry or default_registry
    directory = Path(path)
    files = sorted(directory.glob("*.yaml")) + sorted(directory.glob("*.yml"))
    for f in files:
        if filenames is not None and f.name not in filenames:
            continue
        specs = yaml.safe_load(f.read_text(encoding="utf-8")) or []
        for spec in specs:
            rule = compile_rule(spec)
            if rule.id not in {r.id for r in reg.all()}:
                reg.register(rule, tags=spec.get("tags", ()), rulesets=spec.get("rulesets", ("default",)))
    return reg


def load_entry_points(registry: RuleRegistry | None = None) -> RuleRegistry:
    """Load rules from third-party packages via the stampkit.rules group."""
    reg = registry or default_registry
    for ep in entry_points(group=ENTRY_POINT_GROUP):
        provider = ep.load()
        provider(reg)  # provider is a callable taking the registry
    return reg
