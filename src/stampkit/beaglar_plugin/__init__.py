"""beaglar FreeCAD-bridge plugin (thin layer).

Registers StampKit tools into the bridge's tool router. All logic lives in
stampkit.api; this package only adapts schemas and delegates geometry work to
the CAD instance pool via bridge_api.
"""

from stampkit.beaglar_plugin.bridge_api import PLUGIN_API_VERSION

__all__ = ["PLUGIN_API_VERSION"]
