"""Fix-suggestion templates per rule id.

Declarative rules carry their own ``fix`` template; this module provides
fallbacks for coded rules and richer, context-aware suggestions later.
"""

from __future__ import annotations

_FALLBACK = "调整特征参数以满足 {rule_id}：要求 {required}，当前 {actual}"


def suggest(rule_id: str, actual: float | None, required: float | None, template: str = "") -> str:
    if template:
        return template.format(actual=actual, required=required)
    return _FALLBACK.format(rule_id=rule_id, actual=actual, required=required)
