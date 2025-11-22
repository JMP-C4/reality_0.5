"""Data shapes shared across the hologram pipeline."""

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

Vector3 = Tuple[float, float, float]


@dataclass
class RenderCommand:
    action: str
    payload: Optional[Dict[str, object]] = None
    source: str = "gesture_controller"


@dataclass
class CameraPose:
    name: str
    position: Vector3
    target: Vector3 = (0.0, 0.0, 0.0)
    fov: float = 60.0


@dataclass
class ViewLayout:
    front: str = "front"
    back: str = "back"
    left: str = "left"
    right: str = "right"
    order: Tuple[str, str, str, str] = field(
        default_factory=lambda: ("front", "back", "left", "right")
    )

