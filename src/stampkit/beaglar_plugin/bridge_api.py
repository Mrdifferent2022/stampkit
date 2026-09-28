"""Bridge-side API client: talks to the CAD instance pool.

The plugin handler layer depends only on this module - never on transport
details (stdio vs HTTP), so local and cloud bridge deployments are identical
from StampKit's perspective.
"""

from __future__ import annotations

#: Bump the major version on any breaking change of the plugin contract.
#: The bridge checks compatibility at plugin load time.
PLUGIN_API_VERSION = "1.0"


class BridgeClient:
    """XML-RPC client towards the CAD instance pool. Phase 3."""

    def __init__(self, host: str = "127.0.0.1", port: int = 9875) -> None:
        self.host = host
        self.port = port
