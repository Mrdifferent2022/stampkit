# StampKitPanel addon entry (GUI path). Registers the StampKit workbench.

import Init  # noqa: F401  (ensures sys.path bootstrap runs first)


class StampKitWorkbench(Workbench):  # type: ignore[name-defined]  # FreeCAD injects Workbench
    MenuText = "StampKit"
    ToolTip = "Rapid manufacturability evaluation for sheet metal parts"

    def Initialize(self):
        # Phase 2: register panel commands
        pass

    def GetClassName(self):
        return "Gui::PythonWorkbench"


# Phase 2: Gui.addWorkbench(StampKitWorkbench())
