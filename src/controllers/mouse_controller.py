"""
Controlador de Acciones de Mouse con PyAutoGUI.
"""
import pyautogui
from typing import Optional

class MouseController:
    """
    Gestiona las acciones del mouse como clicks, arrastres y scroll.
    """
    def __init__(self, scroll_amount: int = 200):
        """
        Inicializa el controlador del mouse.

        Args:
            scroll_amount: La cantidad de scroll a aplicar.
        """
        self.scroll_amount = scroll_amount
        self.is_dragging = False
        pyautogui.PAUSE = 0.01
        pyautogui.FAILSAFE = True

    def left_click(self):
        """Realiza un click izquierdo."""
        pyautogui.click()

    def start_drag(self):
        """Inicia un arrastre con el botón izquierdo del mouse."""
        if not self.is_dragging:
            pyautogui.mouseDown()
            self.is_dragging = True

    def release_drag(self):
        """Suelta el arrastre del mouse."""
        if self.is_dragging:
            pyautogui.mouseUp()
            self.is_dragging = False

    def scroll_up(self):
        """Realiza un scroll hacia arriba."""
        pyautogui.scroll(self.scroll_amount)

    def scroll_down(self):
        """Realiza un scroll hacia abajo."""
        pyautogui.scroll(-self.scroll_amount)

    def move_cursor(self, x: int, y: int):
        """
        Mueve el cursor a las coordenadas especificadas.

        Args:
            x: La coordenada X a la que mover el cursor.
            y: La coordenada Y a la que mover el cursor.
        """
        pyautogui.moveTo(x, y)
