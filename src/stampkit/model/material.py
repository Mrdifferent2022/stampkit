"""Material model and builtin material table.

Materials carry the cracking-limit thinning ratio used to normalize
reduced-order-model outputs across material families.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Material:
    name: str
    family: str  # e.g. "aluminum", "steel", "stainless", "copper"
    cracking_limit_thinning: float  # thinning ratio at cracking limit (0..1)

    def __post_init__(self) -> None:
        if not 0.0 < self.cracking_limit_thinning < 1.0:
            raise ValueError("cracking_limit_thinning must be in (0, 1)")


#: Builtin materials; conservative engineering defaults, extend via YAML.
_BUILTIN: dict[str, Material] = {
    "aluminum": Material("aluminum", "aluminum", 0.20),
    "steel": Material("steel", "steel", 0.25),
    "stainless": Material("stainless", "stainless", 0.30),
    "copper": Material("copper", "copper", 0.30),
}


def list_materials() -> list[str]:
    """Names of all builtin materials, sorted."""
    return sorted(_BUILTIN)


def get_material(name: str) -> Material:
    """Look up a builtin material by name (case-insensitive)."""
    key = name.strip().lower()
    try:
        return _BUILTIN[key]
    except KeyError:
        known = ", ".join(sorted(_BUILTIN))
        raise ValueError(f"unknown material {name!r}; known: {known}") from None
