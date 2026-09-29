"""GeometryKernel: the single seam between extraction algorithms and the CAD kernel.

Every architectural boundary hinges on this interface: testability (mock
kernels), process marshalling (implementations run inside a CAD worker while
algorithms run anywhere), and future kernel swaps.

Implementations must be reentrant and must not retain caller-visible mutable
state between calls; ShapeRef handles are opaque and kernel-specific.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from stampkit.model.geometry import BBox, PlaneFrame, Point3, Polyline, Vector3

#: Opaque handle to a kernel-side shape (face, wire, curve, solid...).
ShapeRef = Any


@runtime_checkable
class GeometryKernel(Protocol):
    """Geometric primitives required by the extraction pipeline."""

    # -- import / topology -------------------------------------------------
    def import_step(self, path: str) -> ShapeRef:
        """Import a STEP file; returns a handle to the root shape."""
        ...

    def faces(self, shape: ShapeRef) -> list[ShapeRef]:
        """All faces of a shape."""
        ...

    def is_planar(self, face: ShapeRef) -> bool:
        ...

    def wires(self, face: ShapeRef) -> tuple[ShapeRef, list[ShapeRef]]:
        """(outer wire, inner wires) of a planar face."""
        ...

    def plane_frame(self, face: ShapeRef) -> PlaneFrame:
        """Local frame (origin + normal) of a planar face."""
        ...

    def cylinder_radius(self, face: ShapeRef) -> float | None:
        """Radius if the face is cylindrical, else None."""
        ...

    def cylinder_axis(self, face: ShapeRef) -> tuple[Point3, Vector3] | None:
        """(point on axis, axis direction) if cylindrical, else None."""
        ...

    def cylinder_axial_span(self, face: ShapeRef) -> float | None:
        """Extent of a cylindrical face along its axis."""
        ...

    def has_closed_circle_edge(self, face: ShapeRef) -> bool:
        """True if bounded by a full closed circle (through-hole wall)."""
        ...

    def edge_length(self, edge: ShapeRef) -> float:
        ...

    def shared_edges(self, a: ShapeRef, b: ShapeRef) -> list[ShapeRef]:
        """Edges shared by two faces of the same solid."""
        ...

    def edge_endpoints(self, edge: ShapeRef) -> tuple[Point3, Point3]:
        ...

    def group_connected_faces(self, faces: list[ShapeRef]) -> list[list[int]]:
        """Group face indices by edge-sharing connectivity (union-find)."""
        ...

    def boundary_loop_count(self, faces: list[ShapeRef]) -> int:
        """Closed loops formed by edges used by exactly one face in the group."""
        ...

    def sew(self, faces: list[ShapeRef]) -> list[ShapeRef]:
        """Sew faces into connected open shells; returns the shells."""
        ...

    def face_area(self, face: ShapeRef) -> float:
        ...

    def face_bbox(self, face: ShapeRef) -> BBox:
        ...

    # -- measurements --------------------------------------------------------
    def dist(self, a: ShapeRef, b: ShapeRef) -> float:
        """Minimum distance between two shapes."""
        ...

    def area_of_wire(self, wire: ShapeRef, on: ShapeRef) -> float:
        ...

    def centroid_of_wire(self, wire: ShapeRef, on: ShapeRef) -> Point3:
        ...

    def closest_dist_to_wire(self, wire: ShapeRef, point: Point3) -> float:
        ...

    def control_points(self, wire: ShapeRef, max_points: int) -> list[Point3]:
        ...

    def discretize(self, curve: ShapeRef, tol_mm: float) -> Polyline:
        ...

    def is_closed(self, wire: ShapeRef) -> bool:
        ...

    def nonlinear_edges(self, face: ShapeRef) -> list[ShapeRef]:
        ...

    # -- construction / intersection ------------------------------------------
    def intersects(self, a: ShapeRef, b: ShapeRef) -> bool:
        ...

    def hatch_lines(self, face: ShapeRef, spacing_mm: float, directions: int) -> list[ShapeRef]:
        """Parallel contour lines over the face's bounding surface."""
        ...

    def trim_outside(self, curves: list[ShapeRef], face: ShapeRef) -> list[ShapeRef]:
        """Keep only the parts of curves lying outside the face."""
        ...

    def trim_inside(self, curves: list[ShapeRef], face: ShapeRef) -> list[ShapeRef]:
        ...

    def extrude_curve(self, curve: ShapeRef, direction: Vector3, length: float) -> ShapeRef:
        ...

    def boundary_curves(self, shell: ShapeRef) -> list[ShapeRef]:
        ...
