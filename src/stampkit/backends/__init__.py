"""Kernel backends. This is the ONLY package allowed to import FreeCAD/Part."""

from __future__ import annotations

from stampkit.extraction.kernel import GeometryKernel


class KernelUnavailableError(RuntimeError):
    pass


def get_kernel(name: str = "freecad") -> GeometryKernel:
    """Lazy factory for kernel implementations with an actionable error."""
    if name != "freecad":
        raise KernelUnavailableError(f"unknown kernel {name!r}")
    try:
        from stampkit.backends.freecad_kernel import FreeCadKernel
    except ImportError as e:
        raise KernelUnavailableError(
            "FreeCAD is not available in this Python environment. "
            "Run inside FreeCAD (GUI or freecadcmd), or add FreeCAD's bin "
            "directory to sys.path. See `stampkit doctor`."
        ) from e
    return FreeCadKernel()
