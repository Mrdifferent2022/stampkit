"""Rule engine: registry-based, extensible manufacturability rules.

Three ways to register rules, all funneling into one RuleRegistry:
  1. Code: subclass Rule + @register_rule decorator
  2. Declarative: YAML descriptors compiled to Rule objects
  3. Entry points: third-party packages via the "stampkit.rules" group

Modules in this package MUST NOT import FreeCAD.
"""

from stampkit.rules.base import Rule, RuleScope, Severity
from stampkit.rules.registry import RuleRegistry, register_rule
from stampkit.rules.results import Finding, Verdict

__all__ = [
    "Finding",
    "Rule",
    "RuleRegistry",
    "RuleScope",
    "Severity",
    "Verdict",
    "register_rule",
]
