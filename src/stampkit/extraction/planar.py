"""Planar-face feature extraction.

Holes/slots from inner wires + roundness discrimination; notches/projections
from hatch-line clusters on the outline; relief-cuts by adjacency filtering.
Phase 1 implements holes/slots; Phase 2 the rest.
"""

from __future__ import annotations
