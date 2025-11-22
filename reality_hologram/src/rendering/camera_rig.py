"""Defines camera poses for the four Pepper's Ghost views."""

from typing import Dict

from ..core.events import CameraPose


class CameraRig:
    """Four camera setup for front/back/left/right views."""

    def __init__(self, distance: float = 2.5, height: float = 0.8):
        self.distance = distance
        self.height = height

    def build_views(self) -> Dict[str, CameraPose]:
        """Return camera poses that look at the origin from four sides."""
        return {
            "front": CameraPose("front", (0.0, self.height, self.distance)),
            "back": CameraPose("back", (0.0, self.height, -self.distance)),
            "left": CameraPose("left", (-self.distance, self.height, 0.0)),
            "right": CameraPose("right", (self.distance, self.height, 0.0)),
        }

