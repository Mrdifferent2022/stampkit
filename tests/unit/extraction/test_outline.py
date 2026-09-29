"""Unit tests for 2D outline channel detection (no CAD kernel)."""

from __future__ import annotations

from stampkit.extraction.outline import find_channels, point_in_polygon


def _rect(w: float, h: float) -> list[tuple[float, float]]:
    return [(0, 0), (w, 0), (w, h), (0, h)]


def _dense(pts, step=1.0):
    """Densify a polygon so direction sampling has enough points."""
    import math

    out = []
    n = len(pts)
    for i in range(n):
        a = pts[i]
        b = pts[(i + 1) % n]
        length = math.hypot(b[0] - a[0], b[1] - a[1])
        k = max(1, int(length / step))
        for j in range(k):
            t = j / k
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out


def test_plain_rectangle_has_no_channels():
    assert find_channels(_dense(_rect(100, 80))) == []


def test_l_shape_inner_corner_is_not_a_channel():
    # L outline: inner corner walls are perpendicular, not anti-parallel.
    pts = _dense([(0, 0), (60, 0), (60, 20), (20, 20), (20, 50), (0, 50)])
    assert find_channels(pts) == []


def test_u_notch_detected():
    # 100x80 plate, notch 8 wide x 6 deep on the bottom edge at x=30..38.
    pts = _dense([
        (0, 0), (30, 0), (30, 6), (38, 6), (38, 0), (100, 0), (100, 80), (0, 80),
    ])
    channels = find_channels(pts)
    notches = [c for c in channels if c.kind == "notch"]
    assert len(notches) == 1
    assert abs(notches[0].width_mm - 8.0) < 1.5
    assert abs(notches[0].depth_mm - 6.0) < 1.5


def test_projection_tab_detected():
    # 100x80 plate with a tab 12 wide protruding 10 beyond the right edge.
    pts = _dense([
        (0, 0), (100, 0), (100, 30), (110, 30), (110, 42), (100, 42), (100, 80), (0, 80),
    ])
    channels = find_channels(pts)
    projections = [c for c in channels if c.kind == "projection"]
    assert len(projections) == 1
    assert abs(projections[0].width_mm - 12.0) < 1.5
    assert abs(projections[0].depth_mm - 10.0) < 1.5


def test_two_notches_detected():
    pts = _dense([
        (0, 0), (10, 0), (10, 6), (18, 6), (18, 0),
        (60, 0), (60, 6), (68, 6), (68, 0),
        (100, 0), (100, 80), (0, 80),
    ])
    channels = [c for c in find_channels(pts) if c.kind == "notch"]
    assert len(channels) == 2


def test_point_in_polygon():
    rect = _rect(10, 10)
    assert point_in_polygon((5, 5), rect)
    assert not point_in_polygon((15, 5), rect)


def test_corner_notch_detected():
    # 100x80 plate with a 6 wide x 8 deep recess at the bottom-right corner:
    # the original corner (100, 0) is cut away, leaving a single wall.
    pts = _dense([
        (0, 0), (94, 0), (94, 8), (100, 8), (100, 80), (0, 80),
    ])
    channels = [c for c in find_channels(pts) if c.kind == "notch"]
    assert len(channels) == 1
    assert abs(channels[0].width_mm - 6.0) < 1.5
    assert abs(channels[0].depth_mm - 8.0) < 1.5
    # mouth is reported at the missing original corner
    assert abs(channels[0].mouth_mid[0] - 100.0) < 1.0
    assert abs(channels[0].mouth_mid[1] - 0.0) < 1.0


def test_l_shape_small_leg_is_not_a_corner_channel():
    # L with comparable leg widths: the inner corner must not become a notch.
    pts = _dense([(0, 0), (40, 0), (40, 20), (20, 20), (20, 40), (0, 40)])
    assert find_channels(pts) == []
