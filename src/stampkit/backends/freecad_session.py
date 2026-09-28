"""FreeCAD document lifecycle and extraction-result caching.

Reuses open documents, imports each STEP once, caches ExtractionResult keyed
by (sha256 of file bytes, kernel settings hash). Phase 1.
"""

from __future__ import annotations
