"""ExtractionResult: the boundary type between geometry extraction and evaluation.

Everything an evaluator needs, in JSON-serializable form. No kernel objects
may leak past this boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from stampkit.model.features import Feature


@dataclass(slots=True)
class ExtractionResult:
    features: list[Feature] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    #: Hash of the source geometry, used for caching.
    source_hash: str = ""

    def by_kind(self) -> dict[str, list[Feature]]:
        grouped: dict[str, list[Feature]] = {}
        for f in self.features:
            grouped.setdefault(f.kind.value, []).append(f)
        return grouped
