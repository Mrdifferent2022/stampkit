"""FreeCAD/OCCT implementation of GeometryKernel.

Works identically inside FreeCAD GUI, freecadcmd, and standalone CPython with
FreeCAD's bin on sys.path. Implementation lands in Phase 1.
"""

from __future__ import annotations

import FreeCAD  # noqa: F401  (import here intentionally; backends is the FreeCAD zone)


class FreeCadKernel:
    """GeometryKernel over FreeCAD's Part module / OCCT."""

    # Phase 1: import_step, faces, is_planar, wires, distances, control points.
    # Phase 2: sew, hatch lines, trims, extrusion, boundary curves.
