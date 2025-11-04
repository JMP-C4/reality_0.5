"""
Tests para el Servicio de Mapeo de Gestos.
"""
import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from unittest.mock import Mock
from src.services.gesture_mapper import GestureMapper

class MockLandmark:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class TestGestureMapper(unittest.TestCase):
    """
    Pruebas unitarias para el GestureMapper.
    """
    def setUp(self):
        """Configura el entorno de prueba."""
        self.mapper = GestureMapper()

    def test_detect_gesture_no_landmarks(self):
        """Prueba que no se detecte ningún gesto si no hay landmarks."""
        gesture = self.mapper.detect_gesture(None)
        self.assertIsNone(gesture)

    def test_detect_gesture_fist(self):
        """Prueba la detección del gesto de puño."""
        landmarks = self._create_mock_landmarks(fingers_up=[0, 0, 0, 0, 0])
        gesture = self.mapper.detect_gesture(landmarks)
        self.assertEqual(gesture, "FIST")

    def test_detect_gesture_open_hand(self):
        """Prueba la detección del gesto de mano abierta."""
        landmarks = self._create_mock_landmarks(fingers_up=[1, 1, 1, 1, 1])
        gesture = self.mapper.detect_gesture(landmarks)
        self.assertEqual(gesture, "OPEN_HAND")

    def test_detect_gesture_pointing(self):
        """Prueba la detección del gesto de apuntar."""
        landmarks = self._create_mock_landmarks(fingers_up=[0, 1, 0, 0, 0])
        gesture = self.mapper.detect_gesture(landmarks)
        self.assertEqual(gesture, "POINTING")

    def test_detect_gesture_click(self):
        """Prueba la detección del gesto de click."""
        landmarks = self._create_mock_landmarks(is_click=True)
        gesture = self.mapper.detect_gesture(landmarks)
        self.assertEqual(gesture, "CLICK")

    def _create_mock_landmarks(self, fingers_up=None, is_click=False):
        """Crea un mock de landmarks para simular gestos."""
        mock_landmarks = Mock()
        mock_landmarks.landmark = [MockLandmark(0, 0) for _ in range(21)]

        if fingers_up:
            # Pulgar
            mock_landmarks.landmark[4].x = 0.5 if fingers_up[0] == 1 else 0.6
            mock_landmarks.landmark[3].x = 0.55

            # Otros dedos
            for i in range(1, 5):
                mock_landmarks.landmark[self.mapper.tip_ids[i]].y = 0.4 if fingers_up[i] == 1 else 0.6
                mock_landmarks.landmark[self.mapper.tip_ids[i] - 2].y = 0.5

        if is_click:
            mock_landmarks.landmark[4].x, mock_landmarks.landmark[4].y = 0.5, 0.5
            mock_landmarks.landmark[8].x, mock_landmarks.landmark[8].y = 0.51, 0.51

        return mock_landmarks

if __name__ == "__main__":
    unittest.main()
