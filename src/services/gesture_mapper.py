"""
Servicio de Mapeo de Gestos a partir de Landmarks de Mano.
"""
import numpy as np
from typing import Optional

class GestureMapper:
    """
    Mapea los landmarks de una mano a un gesto específico.
    """
    def __init__(self, click_threshold: float = 0.05):
        """
        Inicializa el mapeador de gestos.

        Args:
            click_threshold: Umbral de distancia para el gesto de click.
        """
        self.tip_ids = [4, 8, 12, 16, 20]
        self.click_threshold = click_threshold

    def detect_gesture(self, hand_landmarks: Optional[any]) -> Optional[str]:
        """
        Detecta un gesto a partir de los landmarks de la mano.

        Args:
            hand_landmarks: Los landmarks de la mano a analizar.

        Returns:
            El nombre del gesto detectado o None si no se reconoce ninguno.
        """
        if not hand_landmarks:
            return None

        landmarks = hand_landmarks

        # --- Contar dedos levantados ---
        fingers_up = self._count_fingers_up(landmarks)
        total_fingers = fingers_up.count(1)

        # --- Detección de gesto de clic ---
        if self._is_click_gesture(landmarks):
            return "CLICK"

        # --- Mapeo de gestos basado en dedos levantados ---
        if total_fingers == 1 and fingers_up[1]:
            return "POINTING"
        if total_fingers == 5:
            return "OPEN_HAND"
        if total_fingers == 0:
            return "FIST"

        return None  # Ningún gesto reconocido

    def _count_fingers_up(self, landmarks: any) -> list[int]:
        """
        Cuenta el número de dedos levantados.
        """
        fingers_up = []
        # Pulgar (eje X)
        if landmarks[self.tip_ids[0]].x < landmarks[self.tip_ids[0] - 1].x:
            fingers_up.append(1)
        else:
            fingers_up.append(0)

        # Otros 4 dedos (eje Y)
        for i in range(1, 5):
            if landmarks[self.tip_ids[i]].y < landmarks[self.tip_ids[i] - 2].y:
                fingers_up.append(1)
            else:
                fingers_up.append(0)
        return fingers_up

    def _is_click_gesture(self, landmarks: any) -> bool:
        """
        Verifica si se está realizando el gesto de click.
        """
        thumb_tip = np.array([landmarks[4].x, landmarks[4].y])
        index_tip = np.array([landmarks[8].x, landmarks[8].y])
        distance = np.linalg.norm(thumb_tip - index_tip)
        return distance < self.click_threshold
