"""Rule contract."""

from __future__ import annotations

import abc
import enum
from typing import TYPE_CHECKING

from stampkit.rules.results import Finding

if TYPE_CHECKING:
    from stampkit.model.context import EvaluationContext
    from stampkit.model.features import Feature, FeatureKind
    from stampkit.rules.world import FeatureWorld


class Severity(enum.StrEnum):
    ERROR = "error"
    WARNING = "warning"


class RuleScope(enum.StrEnum):
    #: Rule checks one feature at a time.
    SINGLE = "single"
    #: Rule checks pairs of features (expanded via FeatureWorld).
    PAIRWISE = "pairwise"


class Rule(abc.ABC):
    """A manufacturability rule.

    Subclasses set class attributes and implement :meth:`check`.
    """

    id: str
    feature_kinds: tuple[FeatureKind, ...]
    severity: Severity = Severity.ERROR
    scope: RuleScope = RuleScope.SINGLE
    description: str = ""
    #: For PAIRWISE rules: the kind of the counterpart feature.
    other_kind: FeatureKind | None = None

    @abc.abstractmethod
    def check(
        self,
        feature: Feature,
        ctx: EvaluationContext,
        world: FeatureWorld,
        other: Feature | None = None,
    ) -> list[Finding]:
        """Return findings for ``feature`` (and ``other`` when PAIRWISE)."""
