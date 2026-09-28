"""Geometry value types shared across the whole package.

These are plain, JSON-serializable dataclasses. Everything that crosses a
process boundary (XML-RPC, MCP, cache) is expressed in these types.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Point3:
    x: float
    y: float
    z: float

    def distance_to(self, other: Point3) -> float:
        return math.dist((self.x, self.y, self.z), (other.x, other.y, other.z))


@dataclass(frozen=True, slots=True)
class Vector3:
    x: float
    y: float
    z: float

    def dot(self, other: Vector3) -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z


@dataclass(frozen=True, slots=True)
class PlaneFrame:
    """A planar face's local frame: an origin point and unit normal."""

    origin: Point3
    normal: Vector3


@dataclass(frozen=True, slots=True)
class Polyline:
    """A discretized curve: ordered points, optionally closed."""

    points: tuple[Point3, ...]
    closed: bool = False

    @property
    def length(self) -> float:
        if len(self.points) < 2:
            return 0.0
        total = 0.0
        pairs = zip(self.points, self.points[1:], strict=False)
        total += sum(a.distance_to(b) for a, b in pairs)
        if self.closed:
            total += self.points[-1].distance_to(self.points[0])
        return total


@dataclass(frozen=True, slots=True)
class BBox:
    """Axis-aligned bounding box."""

    xmin: float
    ymin: float
    zmin: float
    xmax: float
    ymax: float
    zmax: float

    @property
    def lengths(self) -> tuple[float, float, float]:
        return (self.xmax - self.xmin, self.ymax - self.ymin, self.zmax - self.zmin)
