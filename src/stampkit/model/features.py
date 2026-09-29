"""Feature model for sheet metal parts.

Nine feature kinds are recognized: five on planar faces (hole, slot, notch,
projection, relief-cut) and four formed from non-planar surfaces (bend,
drawing, emboss, extruded hole).
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field

from stampkit.model.geometry import PlaneFrame, Point3, Polyline


class FeatureKind(enum.StrEnum):
    # Planar-face features
    HOLE = "hole"
    SLOT = "slot"
    NOTCH = "notch"
    PROJECTION = "projection"
    RELIEF_CUT = "relief_cut"
    # Non-planar features
    BEND = "bend"
    DRAWING = "drawing"
    EMBOSS = "emboss"
    EXTRUDED_HOLE = "extruded_hole"


#: Feature families evaluated by the rule engine (shearing-type features).
RULE_EVALUATED_KINDS: frozenset[FeatureKind] = frozenset(
    {
        FeatureKind.HOLE,
        FeatureKind.SLOT,
        FeatureKind.NOTCH,
        FeatureKind.PROJECTION,
        FeatureKind.RELIEF_CUT,
        FeatureKind.BEND,
    }
)

#: Feature families evaluated by the reduced-order-model evaluator.
ROM_EVALUATED_KINDS: frozenset[FeatureKind] = frozenset({FeatureKind.DRAWING})


@dataclass(slots=True)
class Feature:
    """A detected sheet metal feature with its measured parameters.

    ``params`` holds measured quantities keyed by a stable metric name, e.g.
    ``diameter_mm``, ``width_mm``, ``length_mm``, ``radius_mm``,
    ``min_dist_to_edge_mm``, ``depth_mm``, ``mean_curvature``. Rules and ROM
    evaluators read only from this mapping.
    """

    id: str
    kind: FeatureKind
    face_refs: tuple[str, ...] = ()
    outline: Polyline | None = None
    plane: PlaneFrame | None = None
    #: 3D anchor point for visualization (hole centre, notch mouth, bend
    #: middle, ...); UIs and agents place labels/highlights here.
    anchor: Point3 | None = None
    params: dict[str, float] = field(default_factory=dict)

    def param(self, name: str) -> float | None:
        return self.params.get(name)
