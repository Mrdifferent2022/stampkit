"""Integration tests: run the end-to-end pipeline via freecadcmd.

Skipped unless a FreeCAD command-line executable is available (env
STAMPKIT_FREECAD_CMD or the default install location).
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]

_DEFAULT = r"C:\Users\gom\AppData\Local\Programs\FreeCAD 1.1\bin\freecadcmd.exe"


def _freecadcmd() -> str | None:
    env = os.environ.get("STAMPKIT_FREECAD_CMD")
    if env and Path(env).exists():
        return env
    if Path(_DEFAULT).exists():
        return _DEFAULT
    return shutil.which("freecadcmd")


pytestmark = pytest.mark.freecad


@pytest.fixture(scope="module")
def freecadcmd() -> str:
    exe = _freecadcmd()
    if exe is None:
        pytest.skip("freecadcmd not available")
    return exe


def test_end_to_end_via_freecadcmd(freecadcmd: str):
    proc = subprocess.run(
        [freecadcmd, str(REPO / "scripts" / "run_integration.py")],
        capture_output=True,
        text=True,
        timeout=600,
        cwd=REPO,
    )
    print(proc.stdout)
    print(proc.stderr)
    assert proc.returncode == 0, f"integration runner failed:\n{proc.stdout}\n{proc.stderr}"
