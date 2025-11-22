"""Threaded camera capture that feeds frames to a callback."""

import threading
import time
from typing import Callable, Optional

import cv2

from .mediapipe_hand_tracker import MediapipeHandTracker
from ..utils.logger import get_logger

log = get_logger(__name__)


class CameraLoop:
    def __init__(self, camera_index: int, callback: Callable, width: int = 1280, height: int = 720):
        self.camera_index = camera_index
        self.callback = callback
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.cap: Optional[cv2.VideoCapture] = None
        self.tracker = MediapipeHandTracker()
        self.width = width
        self.height = height
        self._consecutive_failures = 0

    def start(self) -> bool:
        if self.running:
            log.info("CameraLoop already running.")
            return True

        self.cap = self._open_camera()
        if not self.cap or not self.cap.isOpened():
            log.error("Cannot open camera index %s (tried MSMF/DSHOW).", self.camera_index)
            return False

        # Try to set a stable resolution to reduce backend quirks.
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        log.info("CameraLoop started at index %s", self.camera_index)
        return True

    def stop(self):
        self.running = False
        if self.thread and self.thread.is_alive() and threading.current_thread() != self.thread:
            self.thread.join(timeout=2.0)
        if self.cap:
            self.cap.release()
        log.info("CameraLoop stopped.")

    def _run(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                self._consecutive_failures += 1
                if self._consecutive_failures >= 10:
                    log.warning("Frame grab failed %s times; swapping backend.", self._consecutive_failures)
                    self._restart_with_alternate_backend()
                time.sleep(0.05)
                continue

            self._consecutive_failures = 0

            frame = cv2.flip(frame, 1)  # mirror for natural UX
            hand_data = self.tracker.process(frame)

            if self.callback:
                self.callback(frame, hand_data)

            time.sleep(0.01)  # small yield to avoid tight loop

    def _open_camera(self, prefer_dshow: bool = True) -> Optional[cv2.VideoCapture]:
        """Try DirectShow first (mas estable), luego MSMF."""
        backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF] if prefer_dshow else [cv2.CAP_MSMF, cv2.CAP_DSHOW]
        for backend in backends:
            cap = cv2.VideoCapture(self.camera_index, backend)
            if cap.isOpened():
                name = "DirectShow" if backend == cv2.CAP_DSHOW else "MSMF"
                log.info("Camera opened with backend: %s", name)
                return cap
        return None

    def _restart_with_alternate_backend(self):
        """Attempt to reopen the camera with the other backend."""
        current_prefer_dshow = not self.cap or self.cap.getBackendName().lower() != "dshow"
        if self.cap:
            self.cap.release()
        self.cap = self._open_camera(prefer_dshow=current_prefer_dshow)
        self._consecutive_failures = 0
        if not self.cap:
            log.error("Could not reopen camera on alternate backend.")
