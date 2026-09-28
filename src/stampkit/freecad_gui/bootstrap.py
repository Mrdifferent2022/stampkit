"""Bootstrap: put the stampkit source tree on sys.path inside FreeCAD.

Safe under freecadcmd (GUI parts are no-ops there). The StampKitPanel addon's
Init.py calls bootstrap() with the repository path.
"""

from __future__ import annotations

import sys
from pathlib import Path


def bootstrap(repo_src: str | Path) -> None:
    src = str(Path(repo_src).resolve())
    if src not in sys.path:
        sys.path.insert(0, src)
