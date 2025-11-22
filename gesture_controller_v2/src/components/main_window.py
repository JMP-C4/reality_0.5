"""Qt GUI for gesture_controller_v2 using the existing architecture as referencia."""

import sys
from pathlib import Path
from PySide6.QtCore import Qt, QProcess
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QFileDialog,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtWidgets import QMainWindow

from ..core.command_bridge import CommandBridge
from ..core.events import GestureEvent
from ..services.camera_worker import CameraWorker
from ..utils.logger import get_logger
from reality_hologram.src.rendering.scene_manager import SceneManager
import mss
import mss.tools
import tempfile
import subprocess
import time
import ctypes

log = get_logger(__name__)


class MainWindow(QMainWindow):
    def __init__(self, camera_index: int = 0):
        super().__init__()
        self.setWindowTitle("Gesture Controller - Holograma")
        self.setGeometry(100, 100, 1000, 620)

        self.command_bridge = CommandBridge()
        self.camera_worker = CameraWorker(camera_index=camera_index)
        self.camera_worker.frame_ready.connect(self.update_frame)
        self.camera_worker.gesture_detected.connect(self.handle_gesture)
        self.camera_worker.error.connect(self.on_error)
        self.hologram_process: QProcess | None = None
        self.hologram_logs: str = ""
        self.scene_manager = SceneManager()
        self.available_scenes = self.scene_manager.list_available()
        self._last_action_time = {"shutdown": 0.0}
        self.selected_video_path: str | None = None
        self.video_files = self._load_video_files()
        # Defaults for actor/terrain if existen
        self.default_actor = "excavator" if "excavator" in self.available_scenes else (self.available_scenes[0] if self.available_scenes else "default")
        self.default_terrain = "ground_terrain_part_1" if "ground_terrain_part_1" in self.available_scenes else (self.available_scenes[0] if self.available_scenes else "default")

        # --- UI layout ---
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        self.setCentralWidget(main_widget)

        title_label = QLabel("Control por Gestos - Holograma (v2)")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Segoe UI", 20, QFont.Bold))
        main_layout.addWidget(title_label)

        center_layout = QHBoxLayout()
        main_layout.addLayout(center_layout)

        # Camera panel
        camera_frame = QFrame()
        camera_frame.setFrameShape(QFrame.StyledPanel)
        camera_frame.setStyleSheet("background-color: #f5f7fb; border-radius: 10px; border: 1px solid #d9e2ef;")

        camera_layout = QVBoxLayout(camera_frame)
        self.camera_label = QLabel("Vista de cámara")
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setStyleSheet(
            "color: #1b1f27; background-color: #ffffff; border: 1px solid #d9e2ef; border-radius: 10px; min-height: 400px;"
        )
        camera_layout.addWidget(self.camera_label)

        self.gesture_status = QLabel("Gesto detectado: ninguno")
        self.gesture_status.setAlignment(Qt.AlignCenter)
        self.gesture_status.setStyleSheet("color: #0c7c3f; padding: 6px; background-color: #e9f6ef; border-radius: 6px; border: 1px solid #cfe8d8;")
        camera_layout.addWidget(self.gesture_status)

        center_layout.addWidget(camera_frame, 3)

        # Legend panel
        legend_frame = QFrame()
        legend_frame.setFrameShape(QFrame.StyledPanel)
        legend_frame.setStyleSheet("background-color: #f3f6fb; border-radius: 10px; color: #1b1f27; border: 1px solid #d9e2ef;")

        legend_layout = QVBoxLayout(legend_frame)
        legend_title = QLabel("Gestos Programados")
        legend_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        legend_title.setAlignment(Qt.AlignCenter)
        legend_layout.addWidget(legend_title)
        self.gesture_list = QListWidget()
        self.gesture_list.addItems(
            [
                "🤚 Mano abierta (dorso al frente) → Avanzar",
                "✊ Puño cerrado → Pausa / Detener actor",
                "🤏 Pinch (pulgar + índice) → Zoom (más fuerza = más zoom)",
                "☝️ Índice extendido → Rotar eje Y (mano derecha: horario / izquierda: antihorario)",
                "✌️ Dos dedos (paz) → Retroceder",
                "🤟 Tres dedos (índice, medio, pulgar) → Reanudar movimiento",
            ]
        )
        legend_layout.addWidget(self.gesture_list)

        center_layout.addWidget(legend_frame, 1)

        # Selector de actor/terreno y modo
        controls_frame = QFrame()
        controls_frame.setFrameShape(QFrame.StyledPanel)
        controls_layout = QVBoxLayout(controls_frame)
        controls_frame.setStyleSheet("background-color: #f9fbff; border-radius: 10px; color: #1b1f27; border: 1px solid #d9e2ef;")

        self.video_button = QPushButton("Seleccionar Video (.mp4)")
        self.video_button.setStyleSheet(self._button_style("#6C63FF"))

        actor_label = QLabel("maquinaria")
        actor_label.setAlignment(Qt.AlignCenter)
        self.actor_combo = QComboBox()
        self.actor_combo.addItems(self.available_scenes or ["default"])
        if self.default_actor in self.available_scenes:
            self.actor_combo.setCurrentText(self.default_actor)
        self.actor_combo.setStyleSheet(self._combo_style())

        terrain_label = QLabel("Terreno (mapa)")
        terrain_label.setAlignment(Qt.AlignCenter)
        self.terrain_combo = QComboBox()
        self.terrain_combo.addItems(self.available_scenes or ["default"])
        if self.default_terrain in self.available_scenes:
            self.terrain_combo.setCurrentText(self.default_terrain)
        self.terrain_combo.setStyleSheet(self._combo_style())

        self.pepper_checkbox = QCheckBox("Vista Pepper (layout cruz)")
        self.pepper_checkbox.setChecked(False)
        self.videobi_checkbox = QCheckBox("Modo VideoBI (actor+terreno+follow)")
        self.videobi_checkbox.setChecked(True)
        self.video_button = QPushButton("Seleccionar Video (.mp4)")
        self.video_button.setStyleSheet(self._button_style("#6C63FF"))
        video_label = QLabel("Video (opcional)")
        video_label.setAlignment(Qt.AlignCenter)
        self.video_combo = QComboBox()
        self.video_combo.addItems(self.video_files or ["Sin video"])
        self.video_combo.setStyleSheet(self._combo_style())

        controls_layout.addWidget(actor_label)
        controls_layout.addWidget(self.actor_combo)
        controls_layout.addWidget(terrain_label)
        controls_layout.addWidget(self.terrain_combo)
        controls_layout.addWidget(self.pepper_checkbox)
        controls_layout.addWidget(self.videobi_checkbox)
        controls_layout.addWidget(video_label)
        controls_layout.addWidget(self.video_combo)
        controls_layout.addWidget(self.video_button)

        center_layout.addWidget(controls_frame, 1)

        # Buttons
        button_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)

        self.start_button = QPushButton("Iniciar detección")
        self.stop_button = QPushButton("Detener")
        self.manual_button = QPushButton("Reproducir Video Seleccionado")
        self.hologram_button = QPushButton("Abrir Holograma")

        self.start_button.setStyleSheet(self._button_style("#4CAF50"))
        self.stop_button.setStyleSheet(self._button_style("#F44336"))
        self.manual_button.setStyleSheet(self._button_style("#2196F3"))
        self.hologram_button.setStyleSheet(self._button_style("#9C27B0"))

        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.manual_button)
        button_layout.addWidget(self.hologram_button)

        self.start_button.clicked.connect(self.start_detection)
        self.stop_button.clicked.connect(self.stop_detection)
        self.manual_button.clicked.connect(self.play_selected_video)
        self.hologram_button.clicked.connect(self.launch_hologram)
        self.video_button.clicked.connect(self.select_video)

    # --------------------------
    # Slots
    # --------------------------
    def start_detection(self):
        if self.camera_worker.isRunning():
            QMessageBox.information(self, "Cámara activa", "La cámara ya está en funcionamiento.")
            return
        self.camera_worker.start()
        QMessageBox.information(self, "Detección iniciada", "El sistema de gestos ha comenzado.")

    def stop_detection(self):
        if self.camera_worker.isRunning():
            self.camera_worker.stop()
            QMessageBox.warning(self, "Detección detenida", "El sistema de gestos ha sido detenido.")
        else:
            QMessageBox.information(self, "Cámara inactiva", "La cámara ya estaba detenida.")

    def show_manual(self):
        # Reutilizado como play_selected_video
        self.play_selected_video()

    def update_frame(self, qt_image):
        pixmap = QPixmap.fromImage(qt_image)
        self.camera_label.setPixmap(pixmap.scaled(self.camera_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def handle_gesture(self, gesture: GestureEvent):
        """Update UI status and forward command to reality pipeline."""
        self.gesture_status.setText(f"Gesto detectado: {gesture.kind} ({gesture.hand})")
        action, payload = self._map_gesture_to_command(gesture)
        if action:
            if not self._can_send(action):
                return
            response = self.command_bridge.send(action, payload)
            log.info("Gesture -> command: %s payload=%s response=%s", action, payload, response)

    def on_error(self, message: str):
        QMessageBox.critical(self, "Error de cámara", message)

    def launch_hologram(self):
        """Open the Panda3D viewer in a separate process."""
        if self.hologram_process and self.hologram_process.state() != QProcess.NotRunning:
            QMessageBox.information(self, "Holograma activo", "La ventana de holograma ya está abierta.")
            return
        self.hologram_logs = ""
        self.hologram_process = QProcess(self)
        self.hologram_process.setProcessChannelMode(QProcess.SeparateChannels)
        self.hologram_process.readyReadStandardError.connect(self._capture_hologram_output)
        self.hologram_process.readyReadStandardOutput.connect(self._capture_hologram_output)
        self.hologram_process.finished.connect(self._hologram_finished)
        self.hologram_process.setProgram(sys.executable)

        scene_fallback = self.terrain_combo.currentText() if self.terrain_combo.count() else (self.available_scenes[0] if self.available_scenes else "default")
        args = ["-m", "reality_hologram.src.viewer"]

        if self.pepper_checkbox.isChecked():
            # Solo actor, sin terreno
            args += ["--pepper", "--actor", self.actor_combo.currentText(), "--scene", self.actor_combo.currentText()]
        elif self.videobi_checkbox.isChecked():
            args += [
                "--videobi",
                "--actor",
                self.actor_combo.currentText(),
                "--terrain",
                self.terrain_combo.currentText(),
                "--scene",
                scene_fallback,
            ]
        else:
            args += ["--scene", scene_fallback, "--spin"]

        # Video: prioridad al seleccionado; si no hay, intenta combo (sin video = ninguno)
        chosen_video = self.selected_video_path
        combo_video = self.video_combo.currentText() if hasattr(self, "video_combo") and self.video_combo.currentText() != "Sin video" else None
        if not chosen_video:
            chosen_video = combo_video
        if chosen_video:
            args += ["--video", chosen_video]

        self.hologram_process.setArguments(args)
        self.hologram_process.start()
        if not self.hologram_process.waitForStarted(2000):
            QMessageBox.critical(self, "Error", "No se pudo lanzar la ventana de holograma.")
        else:
            QMessageBox.information(self, "Holograma", "Ventana de holograma lanzada.")

    def _capture_hologram_output(self):
        if not self.hologram_process:
            return
        self.hologram_logs += bytes(self.hologram_process.readAllStandardError()).decode(errors="ignore")
        self.hologram_logs += bytes(self.hologram_process.readAllStandardOutput()).decode(errors="ignore")

    def _hologram_finished(self, exit_code: int, exit_status):
        if exit_code != 0:
            msg = "La ventana de holograma se cerró con error."
            if self.hologram_logs.strip():
                msg += f"\n\nLog:\n{self.hologram_logs.strip()}"
            QMessageBox.warning(self, "Holograma cerrado", msg)

    # --------------------------
    # Helpers
    # --------------------------
    def _map_gesture_to_command(self, gesture: GestureEvent):
        action = None
        payload = None

        if gesture.kind == "open":
            action = "move"
            payload = {"direction": "forward", "speed": 1.0}
        elif gesture.kind == "fist":
            action = "pause"
            payload = {"target": "actor"}
        elif gesture.kind == "pinch":
            action = "zoom"
            payload = {"delta": gesture.payload.get("strength", 0.1) if gesture.payload else 0.1}
        elif gesture.kind == "point":
            action = "rotate"
            payload = {"axis": "y", "degrees": 10.0 * (gesture.payload.get("direction", 1) if gesture.payload else 1)}
        elif gesture.kind == "two_fingers":
            action = "move"
            payload = {"direction": "back", "speed": 1.0}
        elif gesture.kind == "three_fingers":
            action = "resume"
            payload = {"target": "actor"}
        return action, payload

    def _can_send(self, action: str, cooldown: float = 0.5) -> bool:
        """Avoid spamming the same action (especially shutdown)."""
        now = time.time()
        last = self._last_action_time.get(action, 0.0)
        if now - last < cooldown:
            return False
        self._last_action_time[action] = now
        return True

    def _button_style(self, color):
        return f"""
        QPushButton {{
            background-color: {color};
            border: none;
            border-radius: 8px;
            color: white;
            font-size: 14px;
            padding: 10px 20px;
        }}
        QPushButton:hover {{
            background-color: #333;
        }}
        """

    def _combo_style(self):
        return """
        QComboBox {
            background-color: #f5f7fb;
            border: 1px solid #d0d7e2;
            border-radius: 8px;
            color: #1b1f27;
            padding: 8px 12px;
            min-width: 170px;
            font-weight: 600;
        }
        QComboBox:hover {
            border: 1px solid #7aa2f7;
        }
        QComboBox::drop-down {
            border: 0px;
            width: 28px;
        }
        QComboBox QAbstractItemView {
            background-color: #ffffff;
            border: 1px solid #d0d7e2;
            selection-background-color: #7aa2f7;
            selection-color: #ffffff;
            outline: 0;
        }
        """

    def closeEvent(self, event):
        if self.camera_worker.isRunning():
            self.camera_worker.stop()
        if self.hologram_process and self.hologram_process.state() != QProcess.NotRunning:
            self.hologram_process.terminate()
        super().closeEvent(event)

    def select_video(self):
        """Selector de video .mp4 para el visor; guarda la ruta y actualiza el botón."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar video (.mp4)", "", "Videos (*.mp4)")
        if file_path:
            self.selected_video_path = file_path
            self.video_button.setText(f"Video: {Path(file_path).name}")
        else:
            self.selected_video_path = None
            self.video_button.setText("Seleccionar Video (.mp4)")

    def play_selected_video(self):
        """Lanza el visor del holograma reproduciendo el video seleccionado."""
        chosen_video = self.selected_video_path
        combo_video = self.video_combo.currentText() if hasattr(self, "video_combo") and self.video_combo.currentText() != "Sin video" else None
        if not chosen_video:
            chosen_video = combo_video
        if not chosen_video:
            QMessageBox.information(self, "Video no seleccionado", "Elige un archivo .mp4 para reproducir.")
            return
        self.selected_video_path = chosen_video
        # Abrir con reproductor del sistema (separado de Panda3D)
        try:
            if sys.platform.startswith("win"):
                subprocess.Popen(["start", "", chosen_video], shell=True)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", chosen_video])
            else:
                subprocess.Popen(["xdg-open", chosen_video])
        except Exception as exc:
            QMessageBox.critical(self, "Error al reproducir", f"No se pudo abrir el video.\n{exc}")

    def _load_video_files(self):
        """Busca videos mp4 en rutas conocidas (raíz y reality_hologram/assets)."""
        candidates = []
        roots = [Path("."), Path("reality_hologram/assets")]
        for root in roots:
            if not root.exists():
                continue
            for p in root.glob("**/*.mp4"):
                candidates.append(str(p.resolve()))
        return candidates

    # --------------------------
    # Screen sharing (holograma)
    # --------------------------
    def share_hologram(self):
        """
        Captura solo la ventana del holograma (similar a elegir ventana en Meet).
        Si no encuentra la ventana, captura pantalla completa como respaldo.
        """
        tmp_dir = tempfile.mkdtemp(prefix="holo-share-")
        outfile = f"{tmp_dir}/holograma.png"
        try:
            region = self._find_hologram_window()
            with mss.mss() as sct:
                monitor = region or sct.monitors[1 if len(sct.monitors) > 1 else 0]
                img = sct.grab(monitor)
                mss.tools.to_png(img.rgb, img.size, output=outfile)
            QMessageBox.information(
                self,
                "Compartir holograma",
                (
                    "Captura generada (solo ventana de holograma si se encontró).\n"
                    "Comparte este archivo en Meet/Teams/Zoom al seleccionar 'Compartir ventana'.\n"
                    f"Ruta: {outfile}"
                ),
            )
            try:
                subprocess.Popen(["explorer", outfile])
            except Exception:
                pass
        except Exception as exc:
            QMessageBox.critical(self, "Error al compartir", f"No se pudo capturar la pantalla.\n{exc}")

    def _find_hologram_window(self):
        """Busca una ventana con titulo que contenga 'Holograma' y devuelve bbox para mss."""
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        EnumWindows = user32.EnumWindows
        GetWindowText = user32.GetWindowTextW
        GetWindowTextLength = user32.GetWindowTextLengthW
        IsWindowVisible = user32.IsWindowVisible
        GetWindowRect = user32.GetWindowRect

        targets = []

        @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
        def enum_proc(hwnd, lparam):
            if not IsWindowVisible(hwnd):
                return True
            length = GetWindowTextLength(hwnd)
            if length == 0:
                return True
            buff = ctypes.create_unicode_buffer(length + 1)
            GetWindowText(hwnd, buff, length + 1)
            title = buff.value
            if "holograma" in title.lower():
                rect = ctypes.wintypes.RECT()
                if GetWindowRect(hwnd, ctypes.byref(rect)):
                    targets.append(
                        {
                            "left": rect.left,
                            "top": rect.top,
                            "width": rect.right - rect.left,
                            "height": rect.bottom - rect.top,
                        }
                    )
            return True

        EnumWindows(enum_proc, 0)
        return targets[0] if targets else None
