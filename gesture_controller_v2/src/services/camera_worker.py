"""Qt camera worker with MediaPipe gesture detection and overlay."""

import cv2
import mediapipe as mp
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage

from .mediapipe_hand_tracker import MediapipeHandTracker
from .gesture_mapper import GestureMapper


class CameraWorker(QThread):
    frame_ready = Signal(QImage)
    gesture_detected = Signal(object)  # GestureEvent
    error = Signal(str)

    def __init__(self, camera_index: int = 0, width: int = 1280, height: int = 720, annotate: bool = True):
        super().__init__()
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.annotate = annotate
        self.running = False
        self.cap = None
        self.tracker = MediapipeHandTracker()
        self.mapper = GestureMapper()
        self._hands = mp.solutions.hands
        self._drawer = mp.solutions.drawing_utils
        self._style = mp.solutions.drawing_styles
        self._consecutive_failures = 0

    def run(self):
        self.cap = self._open_camera(prefer_dshow=True)
        if not self.cap or not self.cap.isOpened():
            self.error.emit(f"No se pudo abrir la camara en indice {self.camera_index}")
            return

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        self.running = True
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                self._consecutive_failures += 1
                if self._consecutive_failures >= 10:
                    self._restart_with_alternate_backend()
                continue
            self._consecutive_failures = 0

            frame = cv2.flip(frame, 1)
            result = self.tracker.process(frame)

            gesture = self.mapper.classify(result)
            if gesture:
                self.gesture_detected.emit(gesture)

            if self.annotate and result and result.multi_hand_landmarks:
                for hand_landmarks in result.multi_hand_landmarks:
                    self._drawer.draw_landmarks(
                        frame,
                        hand_landmarks,
                        self._hands.HAND_CONNECTIONS,
                        self._style.get_default_hand_landmarks_style(),
                        self._style.get_default_hand_connections_style(),
                    )
                if gesture:
                    cv2.putText(
                        frame,
                        f"Gesto: {gesture.kind}",
                        (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 255, 0),
                        2,
                        cv2.LINE_AA,
                    )

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            bytes_per_line = ch * w
            image = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.frame_ready.emit(image)

    def stop(self):
        self.running = False
        self.wait()
        if self.cap:
            self.cap.release()

    def _open_camera(self, prefer_dshow: bool = True):
        backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF] if prefer_dshow else [cv2.CAP_MSMF, cv2.CAP_DSHOW]
        for backend in backends:
            cap = cv2.VideoCapture(self.camera_index, backend)
            if cap.isOpened():
                return cap
        return None

    def _restart_with_alternate_backend(self):
        current_backend = self.cap.getBackendName().lower() if self.cap else ""
        prefer_dshow = current_backend != "dshow"
        if self.cap:
            self.cap.release()
        self.cap = self._open_camera(prefer_dshow=prefer_dshow)
        self._consecutive_failures = 0
        if not self.cap:
            self.error.emit("No se pudo reabrir la camara despues de fallos.")
