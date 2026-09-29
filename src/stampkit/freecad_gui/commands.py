"""FreeCAD command registration (StampKit_Evaluate, StampKit_ClearHighlights).

GUI-only module; imported by the StampKitPanel addon's InitGui.py.
"""

from __future__ import annotations

import FreeCAD as App  # type: ignore[import-not-found]
import FreeCADGui as Gui  # type: ignore[import-not-found]


class _EvaluateCommand:
    def GetResources(self) -> dict[str, str]:
        return {
            "MenuText": "Evaluate part",
            "ToolTip": "Run the StampKit manufacturability evaluation on the selected solid",
        }

    def Activated(self) -> None:
        from stampkit.freecad_gui.panel import show_panel

        show_panel()

    def IsActive(self) -> bool:
        return App.ActiveDocument is not None


class _ClearHighlightsCommand:
    def GetResources(self) -> dict[str, str]:
        return {
            "MenuText": "Clear highlights",
            "ToolTip": "Restore original face colors after a StampKit evaluation",
        }

    def Activated(self) -> None:
        from stampkit.freecad_gui.highlight import clear_all

        if App.ActiveDocument is not None:
            clear_all(App.ActiveDocument)

    def IsActive(self) -> bool:
        return App.ActiveDocument is not None


def register_commands() -> list[str]:
    Gui.addCommand("StampKit_Evaluate", _EvaluateCommand())
    Gui.addCommand("StampKit_ClearHighlights", _ClearHighlightsCommand())
    return ["StampKit_Evaluate", "StampKit_ClearHighlights"]
