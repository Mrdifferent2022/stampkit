# StampKitPanel addon entry (GUI path). Registers the StampKit workbench.

import Init  # noqa: F401  (ensures sys.path bootstrap runs first)

import FreeCADGui as Gui


class StampKitWorkbench(Gui.Workbench):
    MenuText = "StampKit"
    ToolTip = "Rapid manufacturability evaluation for sheet metal parts"

    def Initialize(self):
        from stampkit.freecad_gui.commands import register_commands

        commands = register_commands()
        self.appendToolbar("StampKit", commands)
        self.appendMenu("StampKit", commands)

    def GetClassName(self):
        return "Gui::PythonWorkbench"


Gui.addWorkbench(StampKitWorkbench())
