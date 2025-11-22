"""Main orchestrator for gesture detection and command routing."""

import time
from typing import Optional

from ..core.command_bridge import CommandBridge
from ..core.events import GestureEvent
from ..services.camera_loop import CameraLoop
from ..services.gesture_mapper import GestureMapper
from ..utils.logger import get_logger
from reality_hologram.src.rendering.scene_manager import SceneManager

log = get_logger(__name__)


class GestureController:
    def __init__(self, camera_index: int = 0, warmup_frames: int = 5, preview: bool = True):
        self.mapper = GestureMapper()
        self.camera_loop = CameraLoop(camera_index=camera_index, callback=self._handle_frame)
        self.bridge = CommandBridge()
        self._frame_count = 0
        self._warmup_frames = warmup_frames
        self.preview = preview
        self.scene_manager = SceneManager()
        self.scene_ids = self.scene_manager.list_available()
        self.scene_cursor = 0
        self._action_state = {"moving": False, "playing": True}

    def start(self) -> bool:
        log.info("Starting gesture loop (v2)...")
        self.bridge.send("boot", {"scene": "default"})
        return self.camera_loop.start()

    def stop(self):
        log.info("Stopping gesture loop.")
        self.camera_loop.stop()
        self.bridge.send("shutdown")
        if self.preview:
            try:
                import cv2

                cv2.destroyAllWindows()
            except Exception:
                pass

    def _handle_frame(self, frame, hand_data):
        """Handle a frame + hand landmarks emitted by CameraLoop."""
        self._frame_count += 1
        if self._frame_count <= self._warmup_frames:
            return  # let mediapipe settle

        gesture = self.mapper.classify(hand_data)
        if not gesture:
            if self.preview:
                self._show_preview(frame)
            return

        self._dispatch_gesture(gesture)
        if self.preview:
            self._show_preview(frame)

    def _dispatch_gesture(self, gesture: GestureEvent):
        """Translate gesture into pipeline command."""
        action = None
        payload: Optional[dict] = None

        # Mapeo de gestos a controles tipo WASD/rotar/zoom
        if gesture.kind == "open":
            # Adelante (W)
            action = "move"
            payload = {"direction": "forward", "speed": 1.0}
        elif gesture.kind == "fist":
            # Detener
            action = "pause"
            payload = {"target": "actor"}
        elif gesture.kind == "pinch":
            # Zoom
            action = "zoom"
            payload = {"delta": gesture.payload.get("strength", 0.15)}
        elif gesture.kind == "point":
            # Rotar Y (A/D)
            action = "rotate"
            payload = {"axis": "y", "degrees": 12.0 * (gesture.payload.get("direction", 1))}
        elif gesture.kind == "two_fingers":
            # Atrás (S)
            action = "move"
            payload = {"direction": "back", "speed": 1.0}
        elif gesture.kind == "three_fingers":
            # Reanudar movimiento/animación
            action = "resume"
            payload = {"target": "actor"}

        if action:
            response = self.bridge.send(action, payload)
            log.info("Gesture -> command: %s payload=%s response=%s", action, payload, response)
        else:
            log.debug("Gesture ignored: %s", gesture)

    def _show_preview(self, frame):
        """Display the camera feed in a simple OpenCV window."""
        try:
            import cv2

            cv2.imshow("Gesture Controller v2", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                # Stop loop if user presses q while preview window is focused.
                self.stop()
        except Exception as exc:
            log.debug("Preview render failed: %s", exc)

    def _next_scene(self) -> str:
        if not self.scene_ids:
            return "default"
        self.scene_cursor = (self.scene_cursor + 1) % len(self.scene_ids)
        return self.scene_ids[self.scene_cursor]
