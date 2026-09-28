"""Roundness (hole-vs-slot) discrimination tests."""

from __future__ import annotations

import math

from stampkit.extraction.roundness_test import is_round


def test_circle_is_round():
    r = 5.0
    assert is_round(math.pi * r * r, r)


def test_rounded_rectangle_is_not_round():
    # 30x10 rectangle: area 300, centroid-to-outline distance ~5
    assert not is_round(300.0, 5.0)


def test_degenerate_rejected():
    assert not is_round(100.0, 0.0)
