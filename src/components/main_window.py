"""
Ventana Principal de la Aplicación de Control por Gestos.
"""
import cv2
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import QTimer, Qt

from src.services.hand_tracking import HandTracker
from src.services.gesture_mapper import GestureMapper
from src.controllers.gesture_controller import GestureController
from .control_panel import ControlPanel
from .legend_panel import LegendPanel

class MainWindow(QWidget):
    """
    Ventana principal que integra la cámara, detección de gestos y controles.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Control de Gestos Holográficos v0.4")
        self.resize(1200, 700)

        # --- Inicializar componentes ---
        self._init_camera()
        self._init_services()
        self._init_controllers()
        self._init_ui()
        self._setup_timer()

    def _init_camera(self):
        """Inicializa la cámara."""
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise IOError("No se pudo abrir la cámara")

    def _init_services(self):
        """Inicializa los servicios de detección."""
        self.hand_tracker = HandTracker()
        self.gesture_mapper = GestureMapper()

    def _init_controllers(self):
        """Inicializa los controladores de acciones."""
        self.gesture_controller = GestureController()

    def _init_ui(self):
        """Inicializa la interfaz de usuario."""
        self.video_label = QLabel("Iniciando cámara...")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setFixedSize(640, 480)

        self.control_panel = ControlPanel(self)
        self.legend_panel = LegendPanel()

        main_layout = QHBoxLayout(self)
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.video_label)

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.control_panel)
        right_layout.addWidget(self.legend_panel)
        right_layout.addStretch()

        main_layout.addLayout(left_layout, 3)
        main_layout.addLayout(right_layout, 1)
        self.setLayout(main_layout)

    def _setup_timer(self):
        """Configura el temporizador para actualizar frames."""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # ~30 FPS

    def update_frame(self):
        """Actualiza el frame de la cámara y procesa gestos."""
        ret, frame = self.cap.read()
        if not ret:
            return

        frame = cv2.flip(frame, 1)
        
        result = self.hand_tracker.process_frame(frame)
        if result.hand_landmarks:
            gesture = self.gesture_mapper.detect_gesture(result.hand_landmarks[0])
            self.gesture_controller.process_gesture(gesture, result.hand_landmarks[0], frame.shape)

        # Draw landmarks on the frame
        if result.hand_landmarks:
            for landmarks in result.hand_landmarks:
                for landmark in landmarks:
                    x, y = int(landmark.x * frame.shape[1]), int(landmark.y * frame.shape[0])
                    cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)

        self._display_frame(frame)

    def _display_frame(self, frame):
        """Muestra un frame en el QLabel de video."""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        q_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        self.video_label.setPixmap(pixmap.scaled(self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def closeEvent(self, event):
        """Maneja el evento de cierre de ventana."""
        self.timer.stop()
        self.cap.release()
        self.hand_tracker.close()
        cv2.destroyAllWindows()
        event.accept()
