"""Build golden STEP fixtures parametrically. Run with freecadcmd:

    freecadcmd scripts/gen_fixtures.py

Outputs into tests/fixtures/step/:
  plate_a.step     flat plate 100x80 t=3:  5 holes, 2 slots, all Accept
  bracket_b.step   L-bracket t=2.5 R=5:    3 holes, 1 bend, all Accept
  bracket_b2.step  same, one hole 4.0mm from edge (< 2t=5): 1 violation
  plate_a2.step    plate t=3: 2 holes, 1 notch (8x6), 1 tab (12x10), all Accept
  bracket_c.step   bracket t=2.5: 1 bend, 1 relief-cut (6x8 at bend), 1 notch
  plate_d.step     plate t=2: 1 emboss (dome), 1 drawing (filleted pocket),
                   1 extruded hole (boss collar)
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


def build_plate_a2() -> object:
    """Plate t=3: two holes, a notch (8 wide x 6 deep) and a tab (12x10)."""
    t = 3.0
    plate = Part.makeBox(100, 80, t)
    tab = Part.makeBox(10, 12, t, Vector(100, 40, 0))
    plate = plate.fuse(tab).removeSplitter()
    notch = Part.makeBox(8, 7, t + 2, Vector(70, -1, -1))
    plate = plate.cut(notch)
    for x, y in [(20, 20), (45, 20)]:
        plate = _cut_hole(plate, x, y, 5.0)
    return plate


def build_bracket_c() -> object:
    """Bracket t=2.5 R=5 with a relief-cut (6x8) at the bend tangent and a
    plain notch at the far end of the same edge."""
    t, r = 2.5, 5.0
    wire = _l_profile(r, t, 60.0, 50.0)
    solid = Part.Face(wire).extrude(Vector(0, 40, 0))
    # relief-cut: 6 wide, ending exactly at the bend tangent x=52.5
    solid = solid.cut(Part.makeBox(6, 9, t + 2, Vector(46.5, -1, -1)))
    # plain notch near the free end of the same edge
    solid = solid.cut(Part.makeBox(6, 9, t + 2, Vector(5, -1, -1)))
    return solid


def build_plate_d() -> object:
    """Plate t=2: dome emboss, boss collar (extruded hole), filleted pocket
    (drawing)."""
    t = 2.0
    plate = Part.makeBox(100, 80, t)
    # emboss: spherical dome on the top face (clipped so nothing bulges
    # below the bottom face)
    dome = Part.makeSphere(10.0, Vector(25, 40, t))
    dome = dome.common(Part.makeBox(200, 200, 100, Vector(-50, -50, 0)))
    plate = plate.fuse(dome).removeSplitter()
    # extruded hole: boss collar with a blind hole
    boss = Part.makeCylinder(6.0, 6.0, Vector(60, 40, t))
    boss = boss.cut(Part.makeCylinder(3.0, 5.5, Vector(60, 40, t + 0.5)))
    plate = plate.fuse(boss).removeSplitter()
    # drawing: rectangular pocket with a filleted top rim
    plate = plate.cut(Part.makeBox(20, 20, 2.0, Vector(70, 10, 0.5)))
    rim_edges = [
        e
        for e in plate.Edges
        if abs(e.BoundBox.ZMin - t) < 1e-6
        and abs(e.BoundBox.ZMax - t) < 1e-6
        and 19.0 < e.Length < 21.0
    ]
    if len(rim_edges) == 4:
        plate = plate.makeFillet(0.8, rim_edges)
    else:
        print(f"WARNING: expected 4 pocket rim edges, got {len(rim_edges)}; pocket left unfilleted")
    return plate


def main() -> int:
    os.makedirs(OUT_DIR, exist_ok=True)
    fixtures = {
        "plate_a.step": build_plate_a(),
        "bracket_b.step": build_bracket(hole_edge_offset=11.0),
        "bracket_b2.step": build_bracket(hole_edge_offset=4.0),
        "plate_a2.step": build_plate_a2(),
        "bracket_c.step": build_bracket_c(),
        "plate_d.step": build_plate_d(),
    }
    for name, shape in fixtures.items():
        path = os.path.join(OUT_DIR, name)
        shape.exportStep(path)
        print(f"wrote {path}  faces={len(shape.Faces)}")
    return 0


# freecadcmd does not set __name__ to "__main__"; run unconditionally.
main()
