"""Analytic ROM math sanity checks."""

from __future__ import annotations

import math

import pytest

from stampkit.rom.analytic import principal_strain


def test_zero_strain_when_lengths_equal():
    assert principal_strain(10.0, 10.0) == 0.0


def test_strain_is_log_ratio():
    assert principal_strain(10.0, 15.0) == pytest.approx(math.log(1.5))


def test_rejects_nonpositive():
    with pytest.raises(ValueError):
        principal_strain(0.0, 1.0)
