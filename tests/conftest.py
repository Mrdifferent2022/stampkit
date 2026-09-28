"""Shared fixtures."""

from __future__ import annotations

import pytest

from stampkit.model.context import EvaluationContext
from stampkit.model.features import Feature, FeatureKind
from stampkit.model.material import get_material


@pytest.fixture()
def ctx() -> EvaluationContext:
    return EvaluationContext(thickness_mm=2.5, material=get_material("steel"))


@pytest.fixture()
def make_feature():
    def _make(kind: FeatureKind, fid: str, **params: float) -> Feature:
        return Feature(id=fid, kind=kind, params=dict(params))

    return _make
