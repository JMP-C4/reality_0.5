"""Pepper's Ghost renderer backed by Panda3D (offscreen by defecto)."""

from typing import Dict, Mapping, Optional

from ..core.events import ViewLayout


class PepperRenderer:
    """Builds the four view outputs and the cross layout for the pyramid."""

    def __init__(self, layout: Optional[ViewLayout] = None, texture_size: int = 720, enable_panda: bool = True):
        self.layout = layout or ViewLayout()
        self.texture_size = texture_size
        self.enable_panda = enable_panda
        self._base = None
        self._scene_root = None
        self._panda_imported: Optional[bool] = None
        self._Texture = None
        self._ShowBase = None
        self._loadPrcFileData = None

    # --------------------------
    # Public API
    # --------------------------
    def render(self, scene: Dict[str, object], camera_views: Mapping[str, object]) -> Dict[str, object]:
        """Render the scene into four views for the Pepper's Ghost cross layout."""
        if not self.enable_panda:
            return self._stub_payload(scene, camera_views, reason="panda3d_disabled")

        asset_path = scene.get("asset")
        if not asset_path:
            return self._stub_payload(scene, camera_views, reason="missing_asset")

        base = self._ensure_engine()
        if base is None:
            return self._stub_payload(scene, camera_views, reason="engine_init_failed")

        # Reset scene root to avoid stacking models on consecutive renders.
        if self._scene_root:
            self._scene_root.detachNode()
        self._scene_root = base.render.attachNewNode("scene_root")

        try:
            model = base.loader.loadModel(str(asset_path))
        except Exception as exc:  # pragma: no cover - runtime safeguard
            return self._stub_payload(scene, camera_views, reason=f"load_failed:{exc}")

        model.reparentTo(self._scene_root)
        model.setPos(0, 0, 0)

        view_outputs: Dict[str, object] = {}
        for name, pose in camera_views.items():
            tex = self._Texture()
            buffer = base.win.makeTextureBuffer(f"{name}_buffer", self.texture_size, self.texture_size, tex)
            cam = base.makeCamera(buffer)
            cam.reparentTo(self._scene_root)
            cam.setPos(*pose.position)
            cam.lookAt(*pose.target)
            cam.node().getLens().setFov(pose.fov)
            view_outputs[name] = {"buffer": buffer, "texture": tex, "camera": cam, "pose": pose}

        ordered_views = self.compose_cross(view_outputs)
        return {
            "scene": scene,
            "views": ordered_views,
            "layout": self.layout.order,
            "engine": "panda3d",
            "composed_canvas": "cross_layout_ready",
        }

    def compose_cross(self, view_outputs: Mapping[str, object]) -> Dict[str, object]:
        """Keeps the API explicit for the cross layout assembly order."""
        return {name: view_outputs.get(name) for name in self.layout.order}

    # --------------------------
    # Internals
    # --------------------------
    def _ensure_engine(self):
        if self._base:
            return self._base

        if self._panda_imported is False:
            return None

        try:
            from panda3d.core import Texture, loadPrcFileData
            from direct.showbase.ShowBase import ShowBase
        except Exception:
            self._panda_imported = False
            return None

        self._Texture = Texture
        self._ShowBase = ShowBase
        self._loadPrcFileData = loadPrcFileData
        self._panda_imported = True

        try:
            # Offscreen, no audio, enable GLTF/Assimp loader.
            self._loadPrcFileData("", "window-type offscreen")
            self._loadPrcFileData("", "audio-library-name null")
            self._loadPrcFileData("", "load-file-type p3assimp")
            self._base = self._ShowBase(windowType="offscreen")
            self._base.disableMouse()
            return self._base
        except Exception:
            self._panda_imported = False
            return None

    def _stub_payload(self, scene: Dict[str, object], camera_views: Mapping[str, object], reason: str) -> Dict[str, object]:
        """Fallback payload when Panda3D is not available or asset is missing."""
        ordered_views = {name: {"pose": pose, "buffer": None, "texture": None} for name, pose in camera_views.items()}
        ordered_views = self.compose_cross(ordered_views)
        return {
            "scene": scene,
            "views": ordered_views,
            "layout": self.layout.order,
            "engine": "stub",
            "composed_canvas": None,
            "reason": reason,
        }
