"""Evaluation context: everything a rule or evaluator needs besides features."""

from __future__ import annotations

from dataclasses import dataclass, field

from stampkit.model.material import Material


@dataclass(frozen=True, slots=True)
class KernelSettings:
    """Quality/performance knobs for geometry extraction."""

    hatch_spacing_mm: float = 0.75
    hatch_directions: int = 4
    discretization_tol_mm: float = 0.01
    control_point_samples: int = 64
    min_dist_samples: int = 32


@dataclass(frozen=True, slots=True)
class EvaluationContext:
    """Inputs shared by all evaluators for one evaluation run."""

    thickness_mm: float
    material: Material
    ruleset: str = "default"
    kernel_settings: KernelSettings = field(default_factory=KernelSettings)
    tolerances: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.thickness_mm <= 0:
            raise ValueError("thickness_mm must be positive")
