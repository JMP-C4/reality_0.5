"""Map MediaPipe landmarks to high level gesture events."""

from typing import Optional

import numpy as np

from ..core.events import GestureEvent


class GestureMapper:
    def __init__(self, pinch_threshold: float = 0.06, confidence_min: float = 0.5):
        self.pinch_threshold = pinch_threshold
        self.confidence_min = confidence_min

    def classify(self, mediapipe_result) -> Optional[GestureEvent]:
        """Return a GestureEvent or None based on the first detected hand."""
        if not mediapipe_result or not mediapipe_result.multi_hand_landmarks:
            return None

        hand_landmarks = mediapipe_result.multi_hand_landmarks[0]
        if mediapipe_result.multi_handedness:
            handedness = mediapipe_result.multi_handedness[0].classification[0]
            hand_label = handedness.label  # "Left" / "Right"
            confidence = handedness.score
        else:
            hand_label = "Unknown"
            confidence = 0.0
        if confidence < self.confidence_min:
            return None

        tips = [4, 8, 12, 16, 20]
        pip_joints = [3, 6, 10, 14, 18]

        # MediaPipe coords are normalized [0,1]; y increases downward.
        finger_up = []
        for tip_id, pip_id in zip(tips, pip_joints):
            tip = hand_landmarks.landmark[tip_id]
            pip = hand_landmarks.landmark[pip_id]
            finger_up.append(tip.y < pip.y)

        thumb_tip = hand_landmarks.landmark[4]
        index_tip = hand_landmarks.landmark[8]
        pinch_distance = np.linalg.norm(
            np.array([thumb_tip.x, thumb_tip.y]) - np.array([index_tip.x, index_tip.y])
        )

        # Thumb uses x-axis; invert for left hand.
        thumb_up = (
            thumb_tip.x > hand_landmarks.landmark[3].x
            if hand_label == "Right"
            else thumb_tip.x < hand_landmarks.landmark[3].x
        )
        finger_up[0] = thumb_up

        total_up = sum(1 for v in finger_up if v)

        if pinch_distance < self.pinch_threshold:
            strength = float(max(0.0, (self.pinch_threshold - pinch_distance) / self.pinch_threshold))
            return GestureEvent(kind="pinch", hand=hand_label, confidence=confidence, payload={"strength": strength})

        # Gestos
        if total_up == 5:
            return GestureEvent(kind="open", hand=hand_label, confidence=confidence)
        if total_up == 0:
            return GestureEvent(kind="fist", hand=hand_label, confidence=confidence)
        if finger_up[1] and finger_up[2] and total_up == 2:
            # Dos dedos
            return GestureEvent(kind="two_fingers", hand=hand_label, confidence=confidence)
        if total_up == 3:
            return GestureEvent(kind="three_fingers", hand=hand_label, confidence=confidence)
        if total_up == 4:
            return GestureEvent(kind="four_fingers", hand=hand_label, confidence=confidence)
        if finger_up[1] and total_up == 1:
            direction = -1 if hand_label == "Left" else 1
            return GestureEvent(kind="point", hand=hand_label, confidence=confidence, payload={"direction": direction})

        return None
