"""Build golden STEP fixtures parametrically. Run with freecadcmd:

    freecadcmd scripts/gen_fixtures.py

Outputs into tests/fixtures/step/:
  plate_a.step     flat plate 100x80 t=3:  5 holes, 2 slots, all Accept
  bracket_b.step   L-bracket t=2.5 R=5:    3 holes, 1 bend, all Accept
  bracket_b2.step  same, one hole 4.0mm from edge (< 2t=5): 1 violation
"""

from __future__ import annotations

import os

import Part
from FreeCAD import Vector

OUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tests", "fixtures", "step"
)

_Z = Vector(0, 0, 1)


def _cut_hole(solid, x, y, radius, z0=-1, height=10, axis=None):
    axis = axis if axis is not None else _Z
    return solid.cut(Part.makeCylinder(radius, height, Vector(x, y, z0), axis))


def _cut_slot(solid, cx, cy, length, width, height=10):
    """Horizontal stadium-shaped slot centred at (cx, cy)."""
    r = width / 2.0
    box = Part.makeBox(length - width, width, height, Vector(cx - length / 2 + r, cy - r, -1))
    c1 = Part.makeCylinder(r, height, Vector(cx - length / 2 + r, cy, -1))
    c2 = Part.makeCylinder(r, height, Vector(cx + length / 2 - r, cy, -1))
    return solid.cut(box.fuse(c1).fuse(c2))


def build_plate_a() -> object:
    t = 3.0
    plate = Part.makeBox(100, 80, t)
    for x, y in [(20, 20), (40, 20), (60, 20), (25, 50), (55, 50)]:
        plate = _cut_hole(plate, x, y, 5.0)
    plate = _cut_slot(plate, 78, 62, 25, 6)
    plate = _cut_slot(plate, 20, 66, 25, 6)
    return plate


def _l_profile(r_inner: float, t: float, leg_x: float, leg_z: float) -> object:
    """L cross-section wire in the XZ plane with inner/outer bend arcs."""
    import math

    r_out = r_inner + t
    cx, cz = leg_x - r_out, r_inner + t  # shared bend arc centre
    a45 = math.radians(45)
    outer_mid = Vector(cx + r_out * math.cos(a45), 0, cz - r_out * math.sin(a45))
    inner_mid = Vector(cx + r_inner * math.cos(a45), 0, cz - r_inner * math.sin(a45))
    edges = [
        Part.makeLine(Vector(0, 0, 0), Vector(cx, 0, 0)),
        Part.Arc(Vector(cx, 0, 0), outer_mid, Vector(leg_x, 0, cz)).toShape(),
        Part.makeLine(Vector(leg_x, 0, cz), Vector(leg_x, 0, leg_z)),
        Part.makeLine(Vector(leg_x, 0, leg_z), Vector(leg_x - t, 0, leg_z)),
        Part.makeLine(Vector(leg_x - t, 0, leg_z), Vector(leg_x - t, 0, cz)),
        Part.Arc(Vector(leg_x - t, 0, cz), inner_mid, Vector(cx, 0, t)).toShape(),
        Part.makeLine(Vector(cx, 0, t), Vector(0, 0, t)),
        Part.makeLine(Vector(0, 0, t), Vector(0, 0, 0)),
    ]
    return Part.Wire(edges)


def build_bracket(hole_edge_offset: float) -> object:
    """L-bracket t=2.5, inner bend radius 5, legs 60 (x) by 50 (z), width 40."""
    t, r = 2.5, 5.0
    wire = _l_profile(r, t, 60.0, 50.0)
    solid = Part.Face(wire).extrude(Vector(0, 40, 0))
    # horizontal leg holes (through z)
    solid = _cut_hole(solid, 35, 20, 4.0)
    solid = _cut_hole(solid, hole_edge_offset + 4.0, 20, 4.0)
    # vertical leg hole (through x)
    solid = solid.cut(Part.makeCylinder(4.0, 15, Vector(50, 20, 25), Vector(1, 0, 0)))
    return solid


def main() -> int:
    os.makedirs(OUT_DIR, exist_ok=True)
    fixtures = {
        "plate_a.step": build_plate_a(),
        "bracket_b.step": build_bracket(hole_edge_offset=11.0),
        "bracket_b2.step": build_bracket(hole_edge_offset=4.0),
    }
    for name, shape in fixtures.items():
        path = os.path.join(OUT_DIR, name)
        shape.exportStep(path)
        print(f"wrote {path}  faces={len(shape.Faces)}")
    return 0


# freecadcmd does not set __name__ to "__main__"; run unconditionally.
main()
