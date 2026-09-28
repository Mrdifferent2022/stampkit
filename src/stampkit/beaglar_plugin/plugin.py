"""Tool schemas + handlers registered into the beaglar FreeCAD bridge.

Exposed as the `beaglar.freecad_plugins` entry point. Tool names are stable
(mcp__freecad__stampkit_*); schemas evolve additively only. Phase 3.
"""

from __future__ import annotations

from stampkit.beaglar_plugin.bridge_api import PLUGIN_API_VERSION

TOOLS: list[dict[str, object]] = [
    {
        "name": "stampkit_evaluate",
        "description": "Evaluate a sheet metal part (STEP + thickness + material) "
        "and return a machine-readable manufacturability report.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "STEP file path"},
                "thickness_mm": {"type": "number", "exclusiveMinimum": 0},
                "material": {"type": "string"},
                "ruleset": {"type": "string", "default": "default"},
            },
            "required": ["thickness_mm", "material"],
        },
    },
    {
        "name": "stampkit_list_rules",
        "description": "List registered manufacturability rules.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "stampkit_highlight_violations",
        "description": "Highlight violating features in the CAD view.",
        "inputSchema": {
            "type": "object",
            "properties": {"report_path": {"type": "string"}},
        },
    },
]


def register(bridge_registry: object) -> None:
    """Entry point called by the bridge with its plugin registry. Phase 3."""
    raise NotImplementedError("bridge plugin wiring lands in Phase 3")


__all__ = ["PLUGIN_API_VERSION", "TOOLS", "register"]
