"""Core domain model: geometry value types, features, evaluation context.

Modules in this package MUST NOT import FreeCAD or any CAD kernel.
"""

from stampkit.model.context import EvaluationContext
from stampkit.model.extraction_result import ExtractionResult
from stampkit.model.features import Feature, FeatureKind
from stampkit.model.geometry import BBox, PlaneFrame, Point3, Polyline, Vector3
from stampkit.model.material import Material, get_material

__all__ = [
    "BBox",
    "EvaluationContext",
    "ExtractionResult",
    "Feature",
    "FeatureKind",
    "Material",
    "PlaneFrame",
    "Point3",
    "Polyline",
    "Vector3",
    "get_material",
]
