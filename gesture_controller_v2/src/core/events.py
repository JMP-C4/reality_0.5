"""Shared event/data structures for gesture controller v2."""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class GestureEvent:
    kind: str  # e.g., open, fist, pinch, point
    hand: str  # "Left" or "Right" from MediaPipe
    confidence: float
    payload: Optional[Dict[str, float]] = None


@dataclass
class CommandResponse:
    status: str
    detail: Dict[str, object]

