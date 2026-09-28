"""FeatureWorld: spatial index of features for pairwise/neighbor rules."""

from __future__ import annotations

from stampkit.model.features import Feature, FeatureKind


class FeatureWorld:
    """All extracted features with pairwise-distance lookup.

    Pairwise edge distances are precomputed during parameter computation and
    stored under param keys like ``dist_to:<other_id>``. The world exposes
    them to pairwise rules without any geometry kernel involvement.
    """

    def __init__(self, features: list[Feature]) -> None:
        self._features = list(features)
        self._by_id = {f.id: f for f in self._features}

    def all(self) -> list[Feature]:
        return list(self._features)

    def by_kind(self, kind: FeatureKind) -> list[Feature]:
        return [f for f in self._features if f.kind is kind]

    def get(self, feature_id: str) -> Feature | None:
        return self._by_id.get(feature_id)

    def metric_between(self, a: Feature, b: Feature | None, metric: str) -> float | None:
        """Metric value for a pair (e.g. ``edge_dist_mm``), or None."""
        if b is None:
            return a.param(metric)
        return a.params.get(f"{metric}@{b.id}")

    def pairs(self, kind: FeatureKind, other_kind: FeatureKind | None) -> list[tuple[Feature, Feature]]:
        """Unique feature pairs for pairwise rules (i < j, no self-pairs)."""
        left = self.by_kind(kind)
        right = self.by_kind(other_kind or kind)
        out: list[tuple[Feature, Feature]] = []
        for i, a in enumerate(left):
            for b in right:
                if a.id == b.id:
                    continue
                if other_kind is None or other_kind is kind:
                    j = next((k for k, x in enumerate(left) if x.id == b.id), -1)
                    if j <= i:
                        continue
                out.append((a, b))
        return out
