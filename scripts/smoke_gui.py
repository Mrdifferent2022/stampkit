"""GUI smoke test: run with the FreeCAD GUI executable (not freecadcmd):

    FreeCAD.exe scripts/smoke_gui.py

Verifies that the StampKit workbench registers, the panel class builds, and
a real evaluation highlights the violating faces of a loaded fixture. The
process exits hard at the end (os._exit) so no save prompt blocks the run.
"""

from __future__ import annotations

import os
import sys
import traceback

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

failures: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}")
    if not ok:
        failures.append(name)


def main() -> None:
    import FreeCAD as App
    import FreeCADGui as Gui
    import Part

    # 1. Workbench registered by the installed addon.
    workbenches = Gui.listWorkbenches()
    check(
        "workbench registered",
        "StampKitWorkbench" in workbenches,
        f"have={sorted(workbenches)}",
    )
    if "StampKitWorkbench" in workbenches:
        Gui.activateWorkbench("StampKitWorkbench")
        check("workbench activates", App.GuiUp)

    # 2. Commands registered.
    command_names = [c for c in Gui.Command.listAll()]
    check(
        "commands registered",
        "StampKit_Evaluate" in command_names and "StampKit_ClearHighlights" in command_names,
        f"stampkit commands={[c for c in command_names if 'StampKit' in c]}",
    )

    # 3. Panel class builds without showing it.
    from stampkit.freecad_gui.panel import StampKitPanel

    panel = StampKitPanel(Gui.getMainWindow())
    check("panel builds", panel is not None)
    panel.deleteLater()

    # 4. Load the violating fixture, evaluate the in-memory shape, highlight.
    doc = App.newDocument("SmokeGui")
    Part.insert(os.path.join(REPO, "tests", "fixtures", "step", "bracket_b2.step"), doc.Name)
    doc.recompute()
    obj = [o for o in doc.Objects if getattr(o, "Shape", None) is not None][0]
    Gui.ActiveDocument.setEdit(obj.Name)

    from stampkit.api.service import StampKitService
    from stampkit.freecad_gui import highlight

    report = StampKitService().evaluate_shape(obj.Shape, thickness_mm=2.5, material="steel")
    check("evaluation finds the violation", report.summary.to_fix == 1, f"{report.summary}")

    before = list(obj.ViewObject.DiffuseColor)
    n = highlight.apply_highlights(obj.ViewObject, report, len(obj.Shape.Faces))
    after = list(obj.ViewObject.DiffuseColor)
    check("faces highlighted", n > 0 and after != before, f"highlighted={n}")

    highlight.clear_highlights(obj.ViewObject)
    restored = list(obj.ViewObject.DiffuseColor)
    check("colors restored", restored == before)

    App.closeDocument(doc.Name)


try:
    main()
except Exception:
    traceback.print_exc()
    failures.append("exception")

for f in failures:
    print(f"FAILURES: {f}")
sys.stdout.flush()
sys.stderr.flush()
os._exit(1 if failures else 0)
