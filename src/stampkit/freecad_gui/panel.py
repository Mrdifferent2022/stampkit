"""PySide panel for manual in-FreeCAD evaluation.

Shown by the StampKit_Evaluate command. The user picks a solid (current
selection or the first solid in the active document), thickness and material,
then runs the evaluation; violating features are highlighted in the 3D view.
Works standalone in FreeCAD - no beaglar involved.
"""

from __future__ import annotations

import FreeCAD as App  # type: ignore[import-not-found]
import FreeCADGui as Gui  # type: ignore[import-not-found]
from PySide import QtCore, QtWidgets  # type: ignore[import-not-found]

from stampkit.api.service import StampKitService
from stampkit.freecad_gui import highlight
from stampkit.model.material import list_materials

_DIALOG: StampKitPanel | None = None


def show_panel() -> None:
    global _DIALOG
    if _DIALOG is None:
        _DIALOG = StampKitPanel(Gui.getMainWindow())
    _DIALOG.show()
    _DIALOG.raise_()
    _DIALOG.activateWindow()


def _selected_solid() -> object | None:
    """The selected object with a solid shape, else the first in the document."""
    doc = App.ActiveDocument
    if doc is None:
        return None
    for sel in Gui.Selection.getSelection():
        shape = getattr(sel, "Shape", None)
        if shape is not None and getattr(shape, "Solids", None):
            return sel
    for obj in doc.Objects:
        shape = getattr(obj, "Shape", None)
        if shape is not None and getattr(shape, "Solids", None):
            return obj
    return None


class StampKitPanel(QtWidgets.QDialog):
    def __init__(self, parent: object | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("StampKit - Sheet Metal DFM")
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowType.WindowStaysOnTopHint)
        self._service = StampKitService()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)

        form = QtWidgets.QFormLayout()
        self.part_label = QtWidgets.QLabel("-")
        self.thickness = QtWidgets.QDoubleSpinBox()
        self.thickness.setRange(0.1, 20.0)
        self.thickness.setDecimals(2)
        self.thickness.setSingleStep(0.5)
        self.thickness.setValue(2.0)
        self.thickness.setSuffix(" mm")
        self.material = QtWidgets.QComboBox()
        self.material.addItems(list_materials())
        form.addRow("Part:", self.part_label)
        form.addRow("Thickness:", self.thickness)
        form.addRow("Material:", self.material)
        layout.addLayout(form)

        buttons = QtWidgets.QHBoxLayout()
        self.run_button = QtWidgets.QPushButton("Evaluate")
        self.run_button.clicked.connect(self._on_evaluate)
        self.clear_button = QtWidgets.QPushButton("Clear highlights")
        self.clear_button.clicked.connect(self._on_clear)
        buttons.addWidget(self.run_button)
        buttons.addWidget(self.clear_button)
        layout.addLayout(buttons)

        self.summary_label = QtWidgets.QLabel("")
        layout.addWidget(self.summary_label)

        self.results = QtWidgets.QTreeWidget()
        self.results.setHeaderLabels(["Rule", "Feature", "Verdict", "Actual", "Required"])
        self.results.setRootIsDecorated(False)
        self.results.setAlternatingRowColors(True)
        self.results.itemSelectionChanged.connect(self._on_result_selected)
        layout.addWidget(self.results)

        self.suggestion_label = QtWidgets.QTextEdit()
        self.suggestion_label.setReadOnly(True)
        self.suggestion_label.setMaximumHeight(80)
        layout.addWidget(self.suggestion_label)

        self.resize(560, 520)

    def showEvent(self, event: object) -> None:  # noqa: N802 (Qt override)
        super().showEvent(event)
        self._refresh_part_label()

    def _refresh_part_label(self) -> None:
        obj = _selected_solid()
        self.part_label.setText(f"{obj.Label} ({obj.Name})" if obj is not None else "<no solid>")

    def _on_evaluate(self) -> None:
        obj = _selected_solid()
        if obj is None:
            self.summary_label.setText("No solid found - open a part or select one.")
            return
        self._refresh_part_label()
        highlight.clear_all(obj.Document)
        try:
            report = self._service.evaluate_shape(
                obj.Shape,
                thickness_mm=float(self.thickness.value()),
                material=self.material.currentText(),
            )
        except Exception as exc:  # surface geometry errors to the user
            self.summary_label.setText(f"Evaluation failed: {exc}")
            return
        self._fill_results(report)
        n = highlight.apply_highlights(obj.ViewObject, report, len(obj.Shape.Faces))
        summary = report.summary
        self.summary_label.setText(
            f"{summary.total_features} features, {summary.accepted} accepted, "
            f"{summary.to_fix} to fix ({n} faces highlighted)"
            + (f" | warnings: {'; '.join(report.warnings)}" if report.warnings else "")
        )

    def _fill_results(self, report: object) -> None:
        self.results.clear()
        for finding in report.findings:
            if finding.verdict == "accept":
                continue
            item = QtWidgets.QTreeWidgetItem(
                [
                    finding.rule_id,
                    finding.feature_id,
                    finding.verdict,
                    "-" if finding.actual is None else f"{finding.actual:.2f}",
                    "-" if finding.required is None else f"{finding.required:.2f}",
                ]
            )
            item.setToolTip(0, finding.message)
            item.setData(0, QtCore.Qt.ItemDataRole.UserRole, finding.fix_suggestion)
            self.results.addTopLevelItem(item)
        for col in range(self.results.columnCount()):
            self.results.resizeColumnToContents(col)

    def _on_result_selected(self) -> None:
        items = self.results.selectedItems()
        self.suggestion_label.setPlainText(
            items[0].data(0, QtCore.Qt.ItemDataRole.UserRole) if items else ""
        )

    def _on_clear(self) -> None:
        doc = App.ActiveDocument
        if doc is not None:
            highlight.clear_all(doc)
        self.results.clear()
        self.suggestion_label.clear()
        self.summary_label.setText("")
