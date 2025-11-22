"""Wrapper around MediaPipe Hands for gesture_controller_v2."""

import cv2
import mediapipe as mp


class MediapipeHandTracker:
    def __init__(self, max_hands: int = 2, detection_confidence: float = 0.6, tracking_confidence: float = 0.5):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_hands,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence,
        )

    def process(self, frame):
        """Return MediaPipe result object after RGB conversion."""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return self.hands.process(rgb)

