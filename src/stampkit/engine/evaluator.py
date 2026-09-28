"""Evaluator interface and kind-based routing registry."""

from __future__ import annotations

import abc
from collections.abc import Iterable

from stampkit.model.context import EvaluationContext
from stampkit.model.extraction_result import ExtractionResult
from stampkit.model.features import FeatureKind
from stampkit.rules.results import Finding


class Evaluator(abc.ABC):
    """Evaluates a subset of feature kinds. Implementations must be
    CAD-kernel-free: they consume ExtractionResult, not kernel objects."""

    name: str

    @abc.abstractmethod
    def kinds(self) -> frozenset[FeatureKind]:
        """Feature kinds this evaluator handles."""

    @abc.abstractmethod
    def evaluate(self, extraction: ExtractionResult, ctx: EvaluationContext) -> list[Finding]:
        """Produce findings for the features of the handled kinds."""


class EvaluatorRegistry:
    """Routes feature kinds to evaluators; first registration wins per kind."""

    def __init__(self) -> None:
        self._by_kind: dict[FeatureKind, Evaluator] = {}

    def register(self, evaluator: Evaluator, *, replace: bool = False) -> None:
        for kind in evaluator.kinds():
            if kind in self._by_kind and not replace:
                raise ValueError(
                    f"kind {kind!r} already handled by {self._by_kind[kind].name!r}"
                )
            self._by_kind[kind] = evaluator

    def evaluators_for(self, kinds: Iterable[FeatureKind]) -> list[Evaluator]:
        seen: dict[str, Evaluator] = {}
        for kind in kinds:
            ev = self._by_kind.get(kind)
            if ev is not None:
                seen[ev.name] = ev
        return [seen[k] for k in sorted(seen)]


#: Process-wide default registry.
default_evaluators = EvaluatorRegistry()
