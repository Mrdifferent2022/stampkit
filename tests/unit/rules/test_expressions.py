"""Sandboxed expression evaluation tests."""

from __future__ import annotations

import pytest

from stampkit.rules.expressions import ExpressionError, evaluate_expr


def test_arithmetic():
    assert evaluate_expr("4*t + R", {"t": 2.5, "R": 1.0}) == pytest.approx(11.0)


def test_whitelisted_functions():
    assert evaluate_expr("max(t, R)", {"t": 2.0, "R": 3.0}) == 3.0


def test_rejects_unknown_names():
    with pytest.raises(ExpressionError):
        evaluate_expr("os.system('x')", {})


def test_rejects_attribute_access():
    with pytest.raises(ExpressionError):
        evaluate_expr("t.real", {"t": 1.0})


def test_rejects_import_and_dunder():
    with pytest.raises(ExpressionError):
        evaluate_expr("__import__('os')", {})
