"""Architecture guard: no FreeCAD imports outside backends/ and freecad_gui/."""

from __future__ import annotations

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src" / "stampkit"
ALLOWED_DIRS = {"backends", "freecad_gui"}
FORBIDDEN_ROOTS = ("FreeCAD", "Part", "FreeCADGui")


def _python_files():
    return sorted(SRC.rglob("*.py"))


def test_no_forbidden_kernel_imports_outside_allowed_dirs():
    offenders: list[str] = []
    for path in _python_files():
        rel = path.relative_to(SRC)
        if rel.parts[0] in ALLOWED_DIRS:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            for name in names:
                root = name.split(".")[0]
                if root in FORBIDDEN_ROOTS:
                    offenders.append(f"{rel}: imports {name}")
    assert not offenders, "forbidden CAD-kernel imports found:\n" + "\n".join(offenders)


def test_kernel_protocol_is_importable_without_cad():
    import stampkit.extraction.kernel as k

    assert hasattr(k, "GeometryKernel")
