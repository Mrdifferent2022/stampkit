# StampKitPanel addon entry (headless path).

import os
import sys

# Point this at the StampKit repository's src directory, either by editing
# REPO_SRC or via the STAMPKIT_SRC environment variable.
REPO_SRC = os.environ.get("STAMPKIT_SRC", r"C:\wangjianjun\700.ClaudecodeProject\DFM\src")

if REPO_SRC and REPO_SRC not in sys.path:
    sys.path.insert(0, REPO_SRC)
