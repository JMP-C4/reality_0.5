"""Routes incoming actions into the rendering pipeline."""

from typing import Any, Dict, Optional

from ..core.events import RenderCommand
from ..core.pipeline import RealityPipeline


class CommandRouter:
    """Simple adapter between gesture events and the RealityPipeline."""

    def __init__(self, pipeline: RealityPipeline):
        self.pipeline = pipeline

    def route_command(
        self, action: str, payload: Optional[Dict[str, Any]] = None, source: str = "manual"
    ) -> Dict[str, object]:
        command = RenderCommand(action=action, payload=payload, source=source)
        return self.pipeline.apply_command(command)

