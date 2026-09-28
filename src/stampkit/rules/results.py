"""Findings produced by rules and evaluators."""

from __future__ import annotations

import enum
from dataclasses import dataclass


class Verdict(enum.StrEnum):
    ACCEPT = "accept"
    FIX = "fix"


@dataclass(frozen=True, slots=True)
class Finding:
    """One rule outcome attached to one feature.

    ``actual``/``required`` are numeric when the rule compares a metric, so
    downstream consumers (human UI or an AI agent) can compute the exact
    modification magnitude.
    """

    rule_id: str
    feature_id: str
    verdict: Verdict
    actual: float | None = None
    required: float | None = None
    message: str = ""
    fix_suggestion: str = ""
    severity: str = "error"
    #: Which evaluator produced this finding ("rules" or "rom").
    evaluator: str = "rules"
