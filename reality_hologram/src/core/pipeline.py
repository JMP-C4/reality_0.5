"""Minimal pipeline that links commands with the rendering stage."""

from pathlib import Path
from typing import Dict, Optional
import json
import time

from ..rendering.camera_rig import CameraRig
from ..rendering.pepper_renderer import PepperRenderer
from ..rendering.scene_manager import SceneManager
from .events import RenderCommand


class RealityPipeline:
    """Bridge between gesture intents and the hologram renderer output."""

    def __init__(self, asset_root: Optional[Path] = None):
        self.scene_manager = SceneManager(asset_root=asset_root)
        self.camera_rig = CameraRig()
        self.renderer = PepperRenderer()
        self.current_scene: Optional[Dict[str, object]] = None
        self.command_file = Path(__file__).resolve().parents[2] / ".commands.json"

    def apply_command(self, command: RenderCommand) -> Dict[str, object]:
        action = command.action.lower()
        payload = command.payload or {}

        if action in {"boot", "load_scene"}:
            scene_id = payload.get("scene", "default")
            self.current_scene = self.scene_manager.load(scene_id)
            return {"status": "scene_loaded", "scene": scene_id}

        if action in {"rotate", "zoom", "move", "pause", "resume"}:
            self._write_command({"action": action, "payload": payload, "ts": time.time()})
            return {"status": "queued", "action": action, "payload": payload}

        if action == "render_frame":
            return self.render_frame()

        if action == "shutdown":
            self.current_scene = None
            return {"status": "stopped"}

        return {"status": "ignored", "reason": f"unknown action: {command.action}"}

    def render_frame(self) -> Dict[str, object]:
        """Produces a placeholder layout for the Pepper's Ghost projection."""
        camera_views = self.camera_rig.build_views()
        scene_state = self.current_scene or {"id": "default", "asset": None}
        return self.renderer.render(scene_state, camera_views)

    def _write_command(self, data: Dict[str, object]) -> None:
        try:
            self.command_file.write_text(json.dumps(data), encoding="utf-8")
        except Exception:
            pass
