"""Smoke test: the installed StampKitPanel addon must put stampkit on
sys.path at FreeCAD startup (console mode runs Mod/*/Init.py).

Run: freecadcmd scripts/smoke_addon.py
"""

from __future__ import annotations

import sys

failures = []

try:
    import stampkit

    print(f"PASS  stampkit importable  version={stampkit.__version__} from={stampkit.__file__}")
except Exception as exc:
    failures.append(f"stampkit import failed: {exc}")

try:
    from stampkit.api.service import StampKitService

    StampKitService()
    print("PASS  StampKitService constructible")
except Exception as exc:
    failures.append(f"service failed: {exc}")

if any("Mod\\StampKitPanel" in p or "Mod/StampKitPanel" in p for p in sys.path):
    print("PASS  addon dir on sys.path")
else:
    # Init.py adds the repo src dir, not the addon dir itself; either is fine.
    if any(p.replace("/", "\\").endswith("DFM\\src") for p in sys.path):
        print("PASS  repo src on sys.path via addon Init.py")
    else:
        failures.append("neither addon dir nor repo src found on sys.path")

for f in failures:
    print(f"FAIL  {f}")
sys.stdout.flush()
sys.stderr.flush()
sys.exit(1 if failures else 0)
