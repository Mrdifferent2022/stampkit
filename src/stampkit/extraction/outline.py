"""Outline channel detection: notches and projections on 2D closed polylines.

The outline is first split into maximal straight segments. A channel is a
pair of anti-parallel segments (the channel walls) sitting close together:
the outline run between them forms a compact bulge. If the chord across the
run endpoints lies OUTSIDE the material the bulge cuts inward -> notch; if it
lies INSIDE, the bulge sticks out -> projection.

Filters separate genuine DFM features from lookalikes:
- anti-parallel walls: plain concave corners (L profiles) are perpendicular;
- depth cap: long peninsulas (bracket legs) exceed it;
- depth/width aspect: shallow slivers beside a real channel are skipped.

Pure 2D geometry - no CAD kernel involvement.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

Pt = tuple[float, float]

MIN_BULGE_POINTS = 6
_ANTI_PARALLEL_DOT = -0.7
_SPLIT_ANGLE_TOL = 0.09  # rad; consecutive-edge bend above this splits a segment
_MIN_WALL_LEN = 1.5  # mm; shorter segments cannot be channel walls


@dataclass(frozen=True, slots=True)
class Channel:
    kind: str  # "notch" | "projection"
    width_mm: float  # chord length across the mouth
    depth_mm: float  # max distance from the bulge to the mouth chord
    mouth_mid: Pt


@dataclass(frozen=True, slots=True)
class _Segment:
    start: int  # polyline index of first point
    end: int  # polyline index of last point (exclusive)
    a: Pt
    b: Pt
    direction: Pt
    length: float


def polygon_signed_area(pts: list[Pt]) -> float:
    area = 0.0
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        area += x1 * y2 - x2 * y1
    return area / 2.0


def point_in_polygon(p: Pt, pts: list[Pt]) -> bool:
    x, y = p
    inside = False
    n = len(pts)
    j = n - 1
    for i in range(n):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def _dist_to_line(p: Pt, a: Pt, b: Pt) -> float:
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    norm = math.hypot(dx, dy)
    if norm < 1e-12:
        return math.hypot(p[0] - ax, p[1] - ay)
    return abs((p[0] - ax) * dy - (p[1] - ay) * dx) / norm


def densify(pts: list[Pt], max_step: float = 1.0) -> list[Pt]:
    """Insert points so no edge of the closed polyline exceeds max_step.

    CAD kernels discretize curved edges but return straight edges as bare
    endpoints; channel detection needs a reasonably dense point cloud.
    """
    n = len(pts)
    if n < 2:
        return pts
    out: list[Pt] = []
    for i in range(n):
        a = pts[i]
        b = pts[(i + 1) % n]
        out.append(a)
        dist = math.hypot(b[0] - a[0], b[1] - a[1])
        m = int(math.ceil(dist / max_step))
        for j in range(1, m):
            f = j / m
            out.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
    return out


def split_segments(pts: list[Pt]) -> list[_Segment]:
    """Split a closed polyline into maximal straight segments."""
    n = len(pts)
    # edge directions
    dirs: list[Pt] = []
    for i in range(n):
        ax, ay = pts[i]
        bx, by = pts[(i + 1) % n]
        dx, dy = bx - ax, by - ay
        norm = math.hypot(dx, dy)
        dirs.append((dx / norm, dy / norm) if norm > 1e-12 else (0.0, 0.0))
    # find a split point (large direction change) to start from, so a straight
    # run is never broken by the index-0 wrap
    start = 0
    for i in range(n):
        d1, d2 = dirs[i - 1], dirs[i]
        if d1[0] * d2[0] + d1[1] * d2[1] < math.cos(_SPLIT_ANGLE_TOL):
            start = i
            break
    segments: list[_Segment] = []
    seg_start = start
    for k in range(1, n + 1):
        i = (start + k) % n
        d_prev = dirs[(i - 1) % n]
        d_cur = dirs[i]
        if d_prev[0] * d_cur[0] + d_prev[1] * d_cur[1] < math.cos(_SPLIT_ANGLE_TOL):
            segments.append(_make_segment(pts, seg_start, i, n))
            seg_start = i
    if seg_start != start or not segments:
        segments.append(_make_segment(pts, seg_start, start, n))
    # merge a tiny first/last pair created by the rotation
    if len(segments) >= 2 and segments[0].start == segments[-1].end % n:
        pass  # segments are already maximal by construction
    return segments


def _make_segment(pts: list[Pt], lo: int, hi: int, n: int) -> _Segment:
    a = pts[lo % n]
    b = pts[hi % n]
    dx, dy = b[0] - a[0], b[1] - a[1]
    norm = math.hypot(dx, dy)
    direction = (dx / norm, dy / norm) if norm > 1e-12 else (0.0, 0.0)
    return _Segment(start=lo % n, end=hi % n, a=a, b=b, direction=direction, length=norm)


def _arc_between(pts: list[Pt], lo: int, hi: int) -> list[Pt]:
    """Polyline points from index lo to hi walking forward (inclusive)."""
    n = len(pts)
    if hi < lo:
        hi += n
    return [pts[k % n] for k in range(lo, hi + 1)]


def _anti_parallel(s1: _Segment, s2: _Segment) -> bool:
    dot = s1.direction[0] * s2.direction[0] + s1.direction[1] * s2.direction[1]
    return dot <= _ANTI_PARALLEL_DOT


def _find_corner_channels(
    pts: list[Pt],
    segments: list[_Segment],
    *,
    max_width_mm: float,
    min_depth_mm: float,
    max_depth_mm: float,
    min_aspect: float,
) -> list[Channel]:
    """Detect recesses opening at a convex corner of the outline.

    A corner recess (e.g. a bend relief-cut ending exactly at the tangent
    edge) has only ONE wall: the outline detours V0 -> V1 -> V2 around the
    missing original corner M, with s1 = V0V1 perpendicular to both adjacent
    edges and s2 = V1V2 parallel to the first edge. The two-wall pass cannot
    see it. The recess is reported with mouth at the missing corner M.
    """
    def dot(a: _Segment, b: _Segment) -> float:
        return a.direction[0] * b.direction[0] + a.direction[1] * b.direction[1]

    out: list[Channel] = []
    m = len(segments)
    for i in range(m):
        sp = segments[i - 1]
        s1 = segments[i]
        s2 = segments[(i + 1) % m]
        sn = segments[(i + 2) % m]
        # alternating perpendiculars: sp _|_ s1 _|_ s2 _|_ sn
        if not (
            abs(dot(sp, s1)) <= 0.3
            and abs(dot(s1, s2)) <= 0.3
            and abs(dot(s2, sn)) <= 0.3
        ):
            continue
        # s2 parallel to sp, sn parallel to s1, but sp _|_ sn (a genuine
        # corner - a plain notch has sp parallel sn and is handled above)
        if abs(dot(sp, s2)) < 0.7 or abs(dot(s1, sn)) < 0.7 or abs(dot(sp, sn)) > 0.3:
            continue
        # the recess must be small compared to the edges it cuts into,
        # otherwise an L-shaped plate corner would look like a huge notch
        if s1.length >= 0.5 * sp.length or s2.length >= 0.5 * sn.length:
            continue
        width = min(s1.length, s2.length)
        depth = max(s1.length, s2.length)
        if not (min_depth_mm <= depth <= max_depth_mm):
            continue
        if width > max_width_mm or depth < min_aspect * width:
            continue
        v0 = s1.a
        v1 = s1.b
        v2 = s2.b
        corner = (v0[0] + (v2[0] - v1[0]), v0[1] + (v2[1] - v1[1]))
        # recess side test: a point nudged from the V0-V2 diagonal towards the
        # missing corner must lie OUTSIDE the material
        mid = ((v0[0] + v2[0]) / 2.0, (v0[1] + v2[1]) / 2.0)
        test = (
            mid[0] + (corner[0] - mid[0]) * 0.15,
            mid[1] + (corner[1] - mid[1]) * 0.15,
        )
        if point_in_polygon(test, pts):
            continue
        out.append(Channel(kind="notch", width_mm=width, depth_mm=depth, mouth_mid=corner))
    return out


def find_channels(
    pts: list[Pt],
    *,
    max_width_mm: float = 30.0,
    min_depth_mm: float = 0.3,
    max_depth_mm: float = 25.0,
    min_aspect: float = 0.2,
) -> list[Channel]:
    """Detect notches/projections on a closed 2D outline."""
    n = len(pts)
    if n < 2 * MIN_BULGE_POINTS:
        return []
    segments = [s for s in split_segments(pts) if s.length >= _MIN_WALL_LEN]
    corner_channels = _find_corner_channels(
        pts,
        segments,
        max_width_mm=max_width_mm,
        min_depth_mm=min_depth_mm,
        max_depth_mm=max_depth_mm,
        min_aspect=min_aspect,
    )

    channels: list[Channel] = []
    seen: set[frozenset[int]] = set()
    for si, s1 in enumerate(segments):
        for sj, s2 in enumerate(segments):
            if sj <= si:
                continue
            if not _anti_parallel(s1, s2):
                continue
            # distance between segment midpoints must be within reach
            m1 = ((s1.a[0] + s1.b[0]) / 2, (s1.a[1] + s1.b[1]) / 2)
            m2 = ((s2.a[0] + s2.b[0]) / 2, (s2.a[1] + s2.b[1]) / 2)
            if math.hypot(m1[0] - m2[0], m1[1] - m2[1]) > max_width_mm * 1.5:
                continue
            # the bulge: the shorter of the two arcs containing both segments
            arc1 = _arc_between(pts, s1.start, s2.end)
            arc2 = _arc_between(pts, s2.start, s1.end)
            bulge = arc1 if len(arc1) <= len(arc2) else arc2
            if len(bulge) < 3 or len(bulge) > n - 3:
                continue
            mouth_a, mouth_b = bulge[0], bulge[-1]
            width = math.hypot(mouth_a[0] - mouth_b[0], mouth_a[1] - mouth_b[1])
            if not (1e-9 < width <= max_width_mm):
                continue
            depth = max(_dist_to_line(p, mouth_a, mouth_b) for p in bulge)
            if not (min_depth_mm <= depth <= max_depth_mm):
                continue
            if depth < min_aspect * width:
                continue
            key = frozenset({si, sj})
            if key in seen:
                continue
            seen.add(key)
            mid = ((mouth_a[0] + mouth_b[0]) / 2.0, (mouth_a[1] + mouth_b[1]) / 2.0)
            kind = "projection" if point_in_polygon(mid, pts) else "notch"
            channels.append(
                Channel(kind=kind, width_mm=width, depth_mm=depth, mouth_mid=mid)
            )
    return channels + corner_channels
