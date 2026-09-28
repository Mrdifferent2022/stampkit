"""FreeCAD/OCCT implementation of GeometryKernel.

Works identically inside FreeCAD GUI, freecadcmd, and standalone CPython with
FreeCAD's bin directory on sys.path. All OCCT objects stay behind ShapeRef
handles; nothing kernel-specific crosses into stampkit.extraction.
"""

from __future__ import annotations

import Part
from FreeCAD import Vector

from stampkit.model.geometry import BBox, PlaneFrame, Point3, Polyline, Vector3


def _v3(p: Vector) -> Point3:
    return Point3(p.x, p.y, p.z)


def _vec(p: Point3 | Vector3) -> Vector:
    return Vector(p.x, p.y, p.z)


class FreeCadKernel:
    """GeometryKernel over FreeCAD's Part module / OCCT."""

    # -- import / topology ---------------------------------------------------

    def import_step(self, path: str) -> object:
        return Part.read(path)

    def faces(self, shape: object) -> list[object]:
        return list(shape.Faces)

    def is_planar(self, face: object) -> bool:
        return isinstance(face.Surface, Part.Plane)

    def plane_frame(self, face: object) -> PlaneFrame:
        surface = face.Surface
        return PlaneFrame(origin=_v3(surface.Position), normal=self._normal(surface))

    @staticmethod
    def _normal(surface: Part.Plane) -> Vector3:
        n = surface.Axis
        return Vector3(n.x, n.y, n.z)

    def wires(self, face: object) -> tuple[object, list[object]]:
        outer = face.OuterWire
        inners = [w for w in face.Wires if not w.isSame(outer)]
        return outer, inners

    def face_area(self, face: object) -> float:
        return float(face.Area)

    def face_bbox(self, face: object) -> BBox:
        bb = face.BoundBox
        return BBox(bb.XMin, bb.YMin, bb.ZMin, bb.XMax, bb.YMax, bb.ZMax)

    def cylinder_radius(self, face: object) -> float | None:
        """Radius of a cylindrical face, or None if not cylindrical."""
        if isinstance(face.Surface, Part.Cylinder):
            return float(face.Surface.Radius)
        return None

    def cylinder_axis(self, face: object) -> tuple[Point3, Vector3] | None:
        if isinstance(face.Surface, Part.Cylinder):
            c = face.Surface.Center
            a = face.Surface.Axis
            return _v3(c), Vector3(a.x, a.y, a.z)
        return None

    def cylinder_axial_span(self, face: object) -> float | None:
        """Extent of a cylindrical face along its axis (bbox projection)."""
        if not isinstance(face.Surface, Part.Cylinder):
            return None
        axis = face.Surface.Axis
        bb = face.BoundBox
        corners = [
            Vector(x, y, z)
            for x in (bb.XMin, bb.XMax)
            for y in (bb.YMin, bb.YMax)
            for z in (bb.ZMin, bb.ZMax)
        ]
        ds = [axis.dot(c) for c in corners]
        return float(max(ds) - min(ds))

    def has_closed_circle_edge(self, face: object) -> bool:
        """True if the face is bounded by a full closed circle (through-hole wall)."""
        return any(isinstance(e.Curve, Part.Circle) and e.isClosed() for e in face.Edges)

    # -- measurements ---------------------------------------------------------

    def dist(self, a: object, b: object) -> float:
        return float(a.distToShape(b)[0])

    def area_of_wire(self, wire: object, on: object) -> float:
        return float(Part.Face(wire).Area)

    def centroid_of_wire(self, wire: object, on: object) -> Point3:
        return _v3(Part.Face(wire).CenterOfMass)

    def closest_dist_to_wire(self, wire: object, point: Point3) -> float:
        return float(wire.distToShape(Part.Vertex(_vec(point)))[0])

    def control_points(self, wire: object, max_points: int) -> list[Point3]:
        edges = wire.Edges
        per_edge = max(2, max_points // max(1, len(edges)))
        points: list[Point3] = []
        for edge in edges:
            pts = edge.discretize(Number=per_edge)
            points.extend(_v3(p) for p in pts)
        return points

    def discretize(self, curve: object, tol_mm: float) -> Polyline:
        pts = curve.discretize(Deflection=tol_mm)
        return Polyline(points=tuple(_v3(p) for p in pts), closed=curve.isClosed())

    def is_closed(self, wire: object) -> bool:
        return bool(wire.isClosed())

    def nonlinear_edges(self, face: object) -> list[object]:
        return [e for e in face.Edges if not isinstance(e.Curve, Part.Line)]

    def edge_length(self, edge: object) -> float:
        return float(edge.Length)

    # -- construction / intersection -------------------------------------------
    # Phase 2 (notch/projection/relief-cut and shell classification).

    def intersects(self, a: object, b: object) -> bool:
        return not a.common(b).isNull()

    def sew(self, faces: list[object]) -> list[object]:
        raise NotImplementedError("Phase 2")

    def hatch_lines(self, face: object, spacing_mm: float, directions: int) -> list[object]:
        raise NotImplementedError("Phase 2")

    def trim_outside(self, curves: list[object], face: object) -> list[object]:
        raise NotImplementedError("Phase 2")

    def trim_inside(self, curves: list[object], face: object) -> list[object]:
        raise NotImplementedError("Phase 2")

    def extrude_curve(self, curve: object, direction: Vector3, length: float) -> object:
        raise NotImplementedError("Phase 2")

    def boundary_curves(self, shell: object) -> list[object]:
        raise NotImplementedError("Phase 2")
