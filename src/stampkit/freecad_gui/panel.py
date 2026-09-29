"""PySide panel for manual in-FreeCAD evaluation.

Shown by the StampKit_Evaluate command. The user picks a solid (current
selection or the first solid in the active document), thickness and material,
then runs the evaluation; violating features are highlighted in the 3D view.
Works standalone in FreeCAD - no beaglar involved.
"""

from __future__ import annotations

import FreeCAD as App  # type: ignore[import-not-found]
import FreeCADGui as Gui  # type: ignore[import-not-found]
from PySide import QtCore, QtGui, QtWidgets  # type: ignore[import-not-found]

from stampkit.api.service import StampKitService
from stampkit.freecad_gui import highlight, markers
from stampkit.model.material import list_materials

_DIALOG: StampKitPanel | None = None
_FEATURE_ID_ROLE = QtCore.Qt.ItemDataRole.UserRole + 1


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
        self._obj: object | None = None
        self._report: object | None = None
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
        self.labels_checkbox = QtWidgets.QCheckBox("3D labels")
        self.labels_checkbox.setChecked(True)
        self.labels_checkbox.toggled.connect(self._on_labels_toggled)
        buttons.addWidget(self.run_button)
        buttons.addWidget(self.clear_button)
        buttons.addWidget(self.labels_checkbox)
        layout.addLayout(buttons)

        self.summary_label = QtWidgets.QLabel("")
        layout.addWidget(self.summary_label)

        self.results = QtWidgets.QTreeWidget()
        self.results.setHeaderLabels(["Item", "Detail", "Verdict", "Actual", "Required"])
        self.results.setRootIsDecorated(True)
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
        highlight.clear_selection()
        markers.clear_markers(obj.Document.Name)
        self._obj = None
        self._report = None
        try:
            report = self._service.evaluate_shape(
                obj.Shape,
                thickness_mm=float(self.thickness.value()),
                material=self.material.currentText(),
            )
        except Exception as exc:  # surface geometry errors to the user
            self.summary_label.setText(f"Evaluation failed: {exc}")
            return
        self._obj = obj
        self._report = report
        self._fill_results(report)
        n = highlight.apply_highlights(obj.ViewObject, report, len(obj.Shape.Faces))
        if self.labels_checkbox.isChecked():
            view = Gui.ActiveDocument.ActiveView
            markers.show_markers(obj.Document.Name, view, markers.build_markers(obj.Shape, report))
        summary = report.summary
        self.summary_label.setText(
            f"{summary.total_features} features, {summary.accepted} accepted, "
            f"{summary.to_fix} to fix ({n} faces highlighted)"
            + (f" | warnings: {'; '.join(report.warnings)}" if report.warnings else "")
        )

    @staticmethod
    def _format_params(params: dict[str, float], limit: int = 3) -> str:
        # skip pairwise distance entries (edge_dist_mm@<id>)
        parts = [f"{k}={v:.2f}" for k, v in params.items() if "@" not in k]
        shown = parts[:limit]
        return ", ".join(shown) + (" …" if len(parts) > limit else "")

    def _fill_results(self, report: object) -> None:
        self.results.clear()

        features_root = QtWidgets.QTreeWidgetItem(
            [f"Features ({len(report.features)})", "", "", "", ""]
        )
        self.results.addTopLevelItem(features_root)
        for feat in report.features:
            item = QtWidgets.QTreeWidgetItem(
                features_root, [feat.id, f"{feat.kind}: {self._format_params(feat.params)}", "", "", ""]
            )
            item.setToolTip(1, self._format_params(feat.params, limit=99))
            item.setData(0, _FEATURE_ID_ROLE, feat.id)

        findings_root = QtWidgets.QTreeWidgetItem(
            [f"Findings ({len(report.findings)})", "", "", "", ""]
        )
        self.results.addTopLevelItem(findings_root)
        for finding in report.findings:
            item = QtWidgets.QTreeWidgetItem(
                findings_root,
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
            item.setData(0, _FEATURE_ID_ROLE, finding.feature_id)
            if finding.verdict == "accept":
                for col in range(5):
                    item.setForeground(col, QtGui.QColor("#888888"))
        findings_root.setExpanded(True)
        features_root.setExpanded(True)
        for col in range(self.results.columnCount()):
            self.results.resizeColumnToContents(col)

    def _on_result_selected(self) -> None:
        items = self.results.selectedItems()
        suggestion = items[0].data(0, QtCore.Qt.ItemDataRole.UserRole) if items else None
        self.suggestion_label.setPlainText(suggestion or "")
        if not items or self._report is None or self._obj is None:
            return
        feature_id = items[0].data(0, _FEATURE_ID_ROLE)
        if not feature_id:
            return
        feature = next((f for f in self._report.features if f.id == feature_id), None)
        if feature is None:
            return
        try:
            if highlight.select_feature(self._obj, feature):
                Gui.SendMsgToActiveView("ViewSelection")  # zoom to the faces
        except Exception:
            pass  # document closed or view gone - selection is best-effort

    def _on_labels_toggled(self, checked: bool) -> None:
        if self._obj is None or self._report is None:
            return
        doc_name = self._obj.Document.Name
        if checked:
            view = Gui.ActiveDocument.ActiveView
            markers.show_markers(doc_name, view, markers.build_markers(self._obj.Shape, self._report))
        else:
            markers.clear_markers(doc_name)

    def _on_clear(self) -> None:
        doc = App.ActiveDocument
        if doc is not None:
            highlight.clear_all(doc)
            markers.clear_markers(doc.Name)
        highlight.clear_selection()
        self.results.clear()
        self.suggestion_label.clear()
        self.summary_label.setText("")
