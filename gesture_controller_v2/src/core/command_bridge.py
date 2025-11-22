"""Bridge between gesture controller and reality_hologram pipeline."""

from typing import Dict, Optional

from reality_hologram.src.controllers.command_router import CommandRouter
from reality_hologram.src.core.pipeline import RealityPipeline


class CommandBridge:
    """Thin helper to route normalized commands into the renderer pipeline."""

    def __init__(self, pipeline: Optional[RealityPipeline] = None):
        self.pipeline = pipeline or RealityPipeline()
        self.router = CommandRouter(pipeline=self.pipeline)

    def send(self, action: str, payload: Optional[Dict[str, object]] = None, source: str = "gesture_controller_v2"):
        return self.router.route_command(action=action, payload=payload, source=source)

