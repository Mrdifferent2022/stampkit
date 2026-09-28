"""StampKitService: the single entry point both manual and AI modes call."""

from __future__ import annotations

from stampkit.api.dto import EvaluateRequest
from stampkit.report.schema import Report


class StampKitService:
    """Facade: resolves the part input, runs extraction + evaluation.

    In worker/headless processes this service owns a kernel directly; the
    bridge plugin instead delegates geometry to a CAD instance pool and calls
    only the evaluation half. Phase 1 wires the local path.
    """

    def evaluate(self, request: EvaluateRequest) -> Report:
        raise NotImplementedError("lands in Phase 1")
