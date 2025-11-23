"""Panda3D viewer with VideoBI mode (actor + terrain grid + follow camera)."""

import argparse
import sys
from pathlib import Path

try:
    import panda3d
    from panda3d.core import (
        AmbientLight,
        Camera,
        CardMaker,
        DirectionalLight,
        Filename,
        NodePath,
        PerspectiveLens,
        loadPrcFileData,
    )
    from direct.showbase.ShowBase import ShowBase
except ImportError:
    print("[viewer] Panda3D no esta instalado. Instala panda3d y panda3d-gltf.")
    sys.exit(1)

try:
    # Loader python de panda3d-gltf (evita dependencia de libgltf.dll)
    from gltf import load_model as gltf_load_model
except ImportError:
    gltf_load_model = None

from .rendering.scene_manager import SceneManager
from .rendering.camera_rig import CameraRig


def parse_args():
    parser = argparse.ArgumentParser(description="Reality Hologram Viewer (Panda3D)")
    parser.add_argument("--scene", type=str, default="default", help="Scene id or asset_id to load.")
    parser.add_argument("--scale", type=float, default=0.8, help="Scale factor for the loaded model.")
    parser.add_argument("--spin", action="store_true", help="Rotate model slowly for demo.")
    parser.add_argument("--pepper", action="store_true", help="Mostrar layout cruz Pepper en la ventana.")
    parser.add_argument("--actor", type=str, help="Modelo de maquinaria (actor) para VideoBI.")
    parser.add_argument("--terrain", type=str, help="Modelo de terreno para VideoBI.")
    parser.add_argument("--videobi", action="store_true", help="Activa modo VideoBI (actor + terreno + camara follow).")
    parser.add_argument("--speed", type=float, default=3.0, help="Velocidad del actor en VideoBI (u/s).")
    parser.add_argument("--video", type=str, help="Ruta a un .mp4 para reproducir en la ventana del holograma.")
    return parser.parse_args()


class Viewer(ShowBase):
    def __init__(
        self,
        scene_path: Path,
        scale: float = 0.8,
        spin: bool = False,
        pepper: bool = False,
        actor_path: Path | None = None,
        terrain_path: Path | None = None,
        videobi: bool = False,
        move_speed: float = 3.0,
        video_path: Path | None = None,
    ):
        # Config Panda3D
        plugin_dir = Path(panda3d.__path__[0])  # site-packages/panda3d
        loadPrcFileData("", "load-file-type p3assimp")
        loadPrcFileData("", "load-file-type p3ffmpeg")
        loadPrcFileData("", f"plugin-path {Filename.from_os_specific(str(plugin_dir))}")
        assets_dir = Path(__file__).resolve().parents[1] / "assets"
        loadPrcFileData("", f"model-path {Filename.from_os_specific(str(assets_dir))}")
        # Ajustes de rendimiento
        loadPrcFileData("", "sync-video 0")
        loadPrcFileData("", "framebuffer-multisample 0")
        loadPrcFileData("", "multisamples 0")
        loadPrcFileData("", "basic-shaders-only 1")

        super().__init__()
        self.disableMouse()

        self.videobi = videobi
        self.pepper_mode = pepper
        self.move_speed = move_speed
        self.actor = None
        self.terrain = None
        self._terrain_clones = []
        self._keys = {"forward": False, "back": False, "left": False, "right": False}
        self._terrain_drop = 0.8
        self._follow_offset = (0, -6.5, 2.8)
        self._terrain_flatten = 0.70  # más acostado (~30%)
        self._tile_overlap = 1.00    # máximo solape para eliminar cualquier rendija
        self._tile_size = (0.0, 0.0)
        self._tile_center_idx = (0, 0)
        self.video_path = video_path
        self.command_file = Path(__file__).resolve().parents[1] / ".commands.json"
        self._cmd_last_ts = 0.0
        self._cmd_move_dir = 0  # -1 back, 0 stop, 1 forward
        self._cmd_paused = False
        self._cmd_zoom_factor = 1.0
        self._speed_mult = 1.0

        if pepper:
            # Actor solo para Pepper (sin terreno), escala grande y centrado
            actor_model = actor_path or scene_path
            self.actor = self._load_np(actor_model, scale=scale * 15.0)
            self.actor.reparentTo(self.render)
            self.actor.setPos(0, 0, 0)
            self.actor.setH(90)
            self._setup_controls()
            self.taskMgr.add(self._update_actor, "actorMoveTask")
        elif videobi:
            # Terreno en malla (3x3)
            if terrain_path:
                self.terrain = self._load_np(terrain_path, scale=0.8)
                self.terrain.reparentTo(self.render)
                self.terrain.setScale(1, 1, self._terrain_flatten)
                self._align_terrain(self.terrain)
                self._tile_terrain(self.terrain, span=1, center_idx=(0, 0))

            # Actor (maquinaria)
            actor_model = actor_path or scene_path
            self.actor = self._load_np(actor_model, scale=scale *0.6)
            self.actor.reparentTo(self.render)
            self._place_actor_on_terrain(self.actor, self.terrain)
            # Orientación frontal por defecto
            self.actor.setH(90)

            self._setup_controls()
            self._setup_follow_camera()
            self.taskMgr.add(self._update_actor, "actorMoveTask")
        else:
            # Modo simple
            self.model = self._load_np(scene_path, scale=scale)
            self.model.reparentTo(self.render)
            self.model.setPos(0, 0, 0)

        # Luces
        ambient = AmbientLight("ambient")
        ambient.setColor((0.35, 0.35, 0.35, 1))
        self.render.setLight(self.render.attachNewNode(ambient))

        sun = DirectionalLight("sun")
        sun.setColor((1.0, 1.0, 1.0, 1))
        sun_np = self.render.attachNewNode(sun)
        sun_np.setHpr(45, -30, 0)
        self.render.setLight(sun_np)

        fill = DirectionalLight("fill")
        fill.setColor((0.6, 0.7, 0.8, 1))
        fill_np = self.render.attachNewNode(fill)
        fill_np.setHpr(-60, -20, 0)
        self.render.setLight(fill_np)

        actor_fill = DirectionalLight("actor_fill")
        actor_fill.setColor((1.2, 1.1, 1.0, 1))
        actor_fill_np = self.render.attachNewNode(actor_fill)
        actor_fill_np.setHpr(10, -45, 0)
        self.render.setLight(actor_fill_np)

        if pepper:
            self._setup_pepper_views()
        if spin and not videobi and not pepper:
            self.taskMgr.add(self._spin_task, "spinTask")
        # Solo carga video en modos no-Pepper para evitar mezclar escena/video
        if video_path and not pepper:
            self._setup_video_plane(video_path)

    # --------------------------
    # Scene helpers
    # --------------------------
    def _load_np(self, model_path: Path, scale: float = 1.0) -> NodePath:
        model_path = Path(model_path)
        if not model_path.exists():
            print(f"[viewer] Archivo no encontrado: {model_path}")
            sys.exit(1)
        model = None
        if gltf_load_model:
            try:
                model = gltf_load_model(str(model_path))
            except Exception as exc:
                print(f"[viewer] gltf loader fallo para {model_path}: {exc}")
        if model is None:
            try:
                model = self.loader.loadModel(str(model_path))
            except Exception as exc:
                print(f"[viewer] p3assimp fallo para {model_path}: {exc}")
        if model is None:
            print(f"[viewer] No se pudo cargar el modelo: {model_path}")
            sys.exit(1)
        if not hasattr(model, "reparentTo"):
            model = NodePath(model)
        model.setScale(scale)
        return model

    # --------------------------
    # Pepper layout
    # --------------------------
    def _setup_pepper_views(self):
        if self.cam and self.cam.node().getDisplayRegion(0):
            self.cam.node().getDisplayRegion(0).setActive(False)

        rig = CameraRig(distance=10.0, height=8.0)
        views = rig.build_views()
        layout = {
            "front": (0.33, 0.66, 0.66, 1.0),
            "back": (0.33, 0.66, 0.0, 0.33),
            "left": (0.0, 0.33, 0.33, 0.66),
            "right": (0.66, 1.0, 0.33, 0.66),
        }
        for name, pose in views.items():
            x0, x1, y0, y1 = layout[name]
            region = self.win.makeDisplayRegion(x0, x1, y0, y1)
            region.setSort(0)
            lens = PerspectiveLens()
            lens.setFov(pose.fov)
            cam = Camera(f"{name}_camera")
            cam.setLens(lens)
            cam_np = self.render.attachNewNode(cam)
            cam_np.setPos(*pose.position)
            cam_np.lookAt(*pose.target)
            region.setCamera(cam_np)

    # --------------------------
    # Spin demo
    # --------------------------
    def _spin_task(self, task):
        if hasattr(self, "model"):
            self.model.setH(self.model.getH() + 20 * globalClock.getDt())
        return task.cont

    # --------------------------
    # VideoBI controls
    # --------------------------
    def _setup_controls(self):
        # Intercambiamos W y S
        self.accept("w", self._set_key, ["back", True])
        self.accept("w-up", self._set_key, ["back", False])
        self.accept("s", self._set_key, ["forward", True])
        self.accept("s-up", self._set_key, ["forward", False])
        self.accept("a", self._set_key, ["left", True])
        self.accept("a-up", self._set_key, ["left", False])
        self.accept("d", self._set_key, ["right", True])
        self.accept("d-up", self._set_key, ["right", False])

    def _set_key(self, key, value):
        self._keys[key] = value

    def _update_actor(self, task):
        if not self.actor:
            return task.cont
        self._poll_commands()
        dt = globalClock.getDt()
        heading = self.actor.getH()
        if self._keys["left"]:
            heading += 90 * dt
        if self._keys["right"]:
            heading -= 90 * dt
        self.actor.setH(heading)

        if not self._cmd_paused:
            move_vec = 0.0
            if self._keys["forward"]:
                move_vec += 1.0
            if self._keys["back"]:
                move_vec -= 1.0
            move_vec += self._cmd_move_dir
            if move_vec != 0:
                dist = move_vec * self.move_speed * self._speed_mult * dt
                self.actor.setY(self.actor, -dist)

        self._update_follow_camera()
        self._ensure_tile_coverage()
        return task.cont

    def _setup_follow_camera(self):
        if not self.actor:
            return
        x, y, z = self._follow_offset
        self.camera.reparentTo(self.actor)
        self.camera.setPos(x, y, z)
        self.camera.lookAt(self.actor)

    def _update_follow_camera(self):
        if not self.actor:
            return
        self.camera.lookAt(self.actor)

    # --------------------------
    # Alignment helpers
    # --------------------------
    def _align_terrain(self, terrain_np: NodePath):
        bounds = terrain_np.getTightBounds()
        if not bounds:
            return
        min_pt, max_pt = bounds
        terrain_np.setPos(0, 0, -min_pt.z - self._terrain_drop)

    def _place_actor_on_terrain(self, actor_np: NodePath, terrain_np: NodePath | None):
        actor_bounds = actor_np.getTightBounds()
        actor_min_z = actor_bounds[0].z if actor_bounds else 0.0
        terrain_top = 0.0
        if terrain_np:
            t_bounds = terrain_np.getTightBounds()
            if t_bounds:
                terrain_top = t_bounds[1].z
        target_z = terrain_top - actor_min_z + 0.05
        actor_np.setPos(0, 0, target_z)

    def _tile_terrain(self, terrain_np: NodePath, span: int = 1, center_idx=(0, 0)):
        bounds = terrain_np.getTightBounds()
        if not bounds:
            return
        min_pt, max_pt = bounds
        width = (max_pt.x - min_pt.x) * self._tile_overlap
        depth = (max_pt.y - min_pt.y) * self._tile_overlap
        self._tile_size = (width, depth)
        if width <= 0 or depth <= 0:
            return
        # Mover el terreno base al centro de la grilla
        cx, cy = center_idx
        base_x = cx * width
        base_y = cy * depth
        terrain_np.setPos(base_x, base_y, terrain_np.getZ())
        self._tile_center_idx = center_idx

        for ix in range(-span, span + 1):
            for iy in range(-span, span + 1):
                if ix == 0 and iy == 0:
                    continue
                clone = terrain_np.copyTo(self.render)
                clone.setPos(base_x + ix * width, base_y + iy * depth, terrain_np.getZ())
                self._terrain_clones.append(clone)

    def _ensure_tile_coverage(self):
        if not self.terrain or self._tile_size == (0.0, 0.0):
            return
        width, depth = self._tile_size
        if width == 0 or depth == 0:
            return
        pos = self.actor.getPos() if self.actor else self.camera.getPos()
        ix = int(round(pos.x / width))
        iy = int(round(pos.y / depth))
        if (ix, iy) != self._tile_center_idx:
            # limpiar clones anteriores
            for c in self._terrain_clones:
                c.removeNode()
            self._terrain_clones.clear()
            # reconstruir alrededor del nuevo centro
            self._tile_terrain(self.terrain, span=1, center_idx=(ix, iy))

    # --------------------------
    # Command polling (bridge with gesture controller)
    # --------------------------
    def _poll_commands(self):
        if not self.command_file.exists():
            return
        try:
            data = self.command_file.read_text(encoding="utf-8")
            import json

            cmd = json.loads(data)
        except Exception:
            return

        ts = cmd.get("ts", 0.0)
        if ts <= self._cmd_last_ts:
            return
        self._cmd_last_ts = ts

        action = cmd.get("action")
        payload = cmd.get("payload", {}) or {}

        if action == "move":
            direction = payload.get("direction", "stop")
            if direction == "forward":
                self._cmd_move_dir = 1
                self._cmd_paused = False
            elif direction == "back":
                self._cmd_move_dir = -1
                self._cmd_paused = False
            else:
                self._cmd_move_dir = 0
        elif action == "rotate" and self.actor:
            deg = float(payload.get("degrees", 0.0))
            self.actor.setH(self.actor.getH() + deg)
        elif action == "zoom":
            delta = float(payload.get("delta", 0.0))
            x, y, z = self._follow_offset
            if delta >= 0:
                factor = max(0.3, 1.0 - delta * 0.5)  # acercar
            else:
                factor = min(3.0, 1.0 + abs(delta) * 0.5)  # alejar
            self._follow_offset = (x, y * factor, z * factor)
            self._setup_follow_camera()
        elif action == "pause":
            self._cmd_paused = True
            self._cmd_move_dir = 0
        elif action == "resume":
            self._cmd_paused = False
        elif action == "accelerate":
            factor = float(payload.get("factor", 0.5))
            self._speed_mult = max(0.5, min(3.0, self._speed_mult + factor))

    def _setup_video_plane(self, video_path: Path):
        """Crea un plano con textura de video (mp4) en la escena."""
        video_path = Path(video_path)
        if not video_path.exists():
            print(f"[viewer] Video no encontrado: {video_path}")
            return
        filename = Filename.from_os_specific(str(video_path))
        tex = self.loader.loadTexture(filename)
        if not tex:
            print(f"[viewer] No se pudo cargar el video: {video_path}")
            return
        if hasattr(tex, "setLoop"):
            tex.setLoop(True)
        if hasattr(tex, "play"):
            tex.play()

        width = tex.getVideoWidth() if hasattr(tex, "getVideoWidth") else tex.getXSize()
        height = tex.getVideoHeight() if hasattr(tex, "getVideoHeight") else tex.getYSize()
        aspect = (width / height) if height else 16 / 9

        cm = CardMaker("video_card")
        cm.setFrame(-5 * aspect, 5 * aspect, -5, 5)  # tamaño regulable
        card = self.render.attachNewNode(cm.generate())
        card.setTexture(tex)
        card.setPos(0, 12, 2)
        card.setBillboardPointEye()
        print(f"[viewer] Video adjuntado: {video_path}")


def main():
    args = parse_args()
    manager = SceneManager()
    scene_info = manager.load(args.scene)
    scene_path = scene_info.get("asset")
    if not scene_path:
        print(f"[viewer] No se encontro asset para scene '{args.scene}'. Disponible: {manager.list_available()}")
        sys.exit(1)

    actor_path = None
    terrain_path = None
    if args.videobi:
        if args.actor:
            actor_path = manager.registry.resolve(args.actor)
        if args.terrain:
            terrain_path = manager.registry.resolve(args.terrain)
        if args.actor and not actor_path:
            print(f"[viewer] No se encontro actor '{args.actor}'. Disponible: {manager.list_available()}")
        if args.terrain and not terrain_path:
            print(f"[viewer] No se encontro terreno '{args.terrain}'. Disponible: {manager.list_available()}")

    viewer = Viewer(
        scene_path=scene_path,
        scale=args.scale,
        spin=args.spin,
        pepper=args.pepper,
        actor_path=actor_path,
        terrain_path=terrain_path,
        videobi=args.videobi,
        move_speed=args.speed,
        video_path=Path(args.video) if args.video else None,
    )
    viewer.run()


if __name__ == "__main__":
    main()
