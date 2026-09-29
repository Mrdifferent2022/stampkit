"""Install the StampKitPanel addon into FreeCAD's Mod directory.

Usage (repo venv or any Python 3.11+):

    python scripts/install_freecad_addon.py [--link] [--uninstall]

Default: copy ``addons/StampKitPanel`` into FreeCAD's per-user Mod
directory. ``--link`` creates a directory junction/symlink instead, so
edits in the repository take effect without reinstalling (developer mode;
on Windows it uses a junction, which needs no admin rights).
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

ADDON_NAME = "StampKitPanel"
REPO_ROOT = Path(__file__).resolve().parent.parent
ADDON_SRC = REPO_ROOT / "addons" / ADDON_NAME


def _user_data_root() -> Path:
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if not appdata:
            raise RuntimeError("APPDATA environment variable is not set")
        return Path(appdata) / "FreeCAD"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "FreeCAD"
    return Path.home() / ".local" / "share" / "FreeCAD"


def mod_dir() -> Path:
    """FreeCAD's per-user Mod directory for the current platform.

    FreeCAD >= 1.0 may use a versioned user dir (e.g. FreeCAD/v1-1); prefer
    the newest existing versioned directory, else the unversioned one.
    """
    root = _user_data_root()
    versioned = sorted(
        (d for d in root.glob("v*-*") if d.is_dir()),
        key=lambda d: d.name,
        reverse=True,
    )
    if versioned:
        return versioned[0] / "Mod"
    return root / "Mod"


def uninstall(target: Path) -> None:
    if target.is_symlink() or target.is_junction():
        target.unlink()
        print(f"removed link {target}")
    elif target.is_dir():
        shutil.rmtree(target)
        print(f"removed {target}")
    else:
        print(f"nothing to remove at {target}")


def install(target: Path, link: bool) -> None:
    if target.exists() or target.is_symlink():
        uninstall(target)
    if link:
        # On Windows a junction works without elevated privileges.
        if sys.platform == "win32":
            import subprocess

            subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(target), str(ADDON_SRC)],
                check=True,
                capture_output=True,
            )
        else:
            target.symlink_to(ADDON_SRC, target_is_directory=True)
        print(f"linked {target} -> {ADDON_SRC}")
    else:
        shutil.copytree(ADDON_SRC, target)
        print(f"copied {ADDON_SRC} -> {target}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--link", action="store_true", help="junction/symlink instead of copy")
    parser.add_argument("--uninstall", action="store_true", help="remove the addon")
    args = parser.parse_args()

    if not ADDON_SRC.is_dir():
        print(f"addon source not found: {ADDON_SRC}", file=sys.stderr)
        return 1

    target = mod_dir() / ADDON_NAME
    if args.uninstall:
        uninstall(target)
        return 0

    target.parent.mkdir(parents=True, exist_ok=True)
    install(target, args.link)

    src_hint = REPO_ROOT / "src"
    print(
        f"\nDone. The addon resolves the stampkit package via the STAMPKIT_SRC\n"
        f"environment variable, defaulting to {src_hint} (already correct).\n"
        f"Restart FreeCAD, then switch to the 'StampKit' workbench."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
