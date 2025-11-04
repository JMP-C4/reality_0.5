"""
Controlador Principal de Gestos que Orquesta Acciones del Sistema.
"""
import time
from typing import Optional, Any
from .mouse_controller import MouseController

class GestureController:
    """
    Procesa gestos y los traduce en acciones de control del mouse.
    """
    def __init__(self, cooldown: float = 0.5):
        """
        Inicializa el controlador de gestos.

        Args:
            cooldown: Tiempo de espera en segundos para evitar acciones repetidas.
        """
        self.mouse_controller = MouseController()
        self.cooldown = cooldown
        self.last_gesture = None
        self.last_gesture_time = 0

        self.gesture_actions = {
            "CLICK": self.mouse_controller.left_click,
            "FIST": self.mouse_controller.start_drag,
            "OPEN_HAND": self.mouse_controller.release_drag,
            "POINTING": self._handle_pointing,
        }

    def process_gesture(self, gesture: Optional[str], hand_landmarks: Optional[Any], frame_shape: tuple):
        """
        Procesa un gesto y ejecuta la acción correspondiente.

        Args:
            gesture: El gesto detectado.
            hand_landmarks: Los landmarks de la mano.
            frame_shape: Las dimensiones del frame de la cámara.
        """
        if not gesture:
            return

        current_time = time.time()
        if gesture == self.last_gesture and (current_time - self.last_gesture_time) < self.cooldown:
            return

        if gesture in self.gesture_actions:
            action = self.gesture_actions[gesture]
            if gesture == "POINTING":
                action(hand_landmarks, frame_shape)
            else:
                action()
            
            self.last_gesture = gesture
            self.last_gesture_time = current_time

    def _handle_pointing(self, hand_landmarks: Any, frame_shape: tuple):
        """
        Maneja el gesto de apuntar para mover el cursor.

        Args:
            hand_landmarks: Los landmarks de la mano.
            frame_shape: Las dimensiones del frame de la cámara.
        """
        if not hand_landmarks:
            return

        # Obtener las coordenadas del dedo índice
        index_finger_tip = hand_landmarks[8]
        h, w, _ = frame_shape
        cx, cy = int(index_finger_tip.x * w), int(index_finger_tip.y * h)

        # Mover el cursor
        self.mouse_controller.move_cursor(cx, cy)
