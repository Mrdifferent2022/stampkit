"""Feature extraction: geometry algorithms written against GeometryKernel only.

Modules in this package MUST NOT import FreeCAD; they depend solely on the
kernel protocol in kernel.py. Kernel implementations live in stampkit.backends.
"""

from stampkit.extraction.kernel import GeometryKernel, ShapeRef

__all__ = ["GeometryKernel", "ShapeRef"]
