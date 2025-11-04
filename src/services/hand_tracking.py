"""
Servicio de Detección y Seguimiento de Manos con MediaPipe.
"""
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

class HandTracker:
    """
    Encapsula la lógica de detección de manos de MediaPipe.
    """
    def __init__(
        self,
        max_hands: int = 1,
        detection_confidence: float = 0.7,
        tracking_confidence: float = 0.7
    ):
        """
        Inicializa el detector de manos.

        Args:
            max_hands: Número máximo de manos a detectar.
            detection_confidence: Confianza mínima para la detección.
            tracking_confidence: Confianza mínima para el seguimiento.
        """
        base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=max_hands,
            min_hand_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence)
        self.landmarker = vision.HandLandmarker.create_from_options(options)

    def process_frame(self, frame: cv2.typing.MatLike):
        """
        Procesa un frame de video para detectar y dibujar manos.

        Args:
            frame: El frame de video a procesar.

        Returns:
            Un objeto HandLandmarkerResult con el frame procesado y los landmarks.
        """
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        detection_result = self.landmarker.detect(mp_image)
        
        return detection_result

    def close(self):
        """
        Libera los recursos del detector de manos.
        """
        self.landmarker.close()
