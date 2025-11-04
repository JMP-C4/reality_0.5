"""
Tests para el Controlador de Mouse.
"""
import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from unittest.mock import patch, MagicMock
from src.controllers.mouse_controller import MouseController

class TestMouseController(unittest.TestCase):
    """
    Pruebas unitarias para el MouseController.
    """
    def setUp(self):
        """Configura el entorno de prueba."""
        self.controller = MouseController()

    @patch('pyautogui.click')
    def test_left_click(self, mock_click):
        """Prueba que se llame al método de click izquierdo."""
        self.controller.left_click()
        mock_click.assert_called_once()

    @patch('pyautogui.mouseDown')
    def test_start_drag(self, mock_mouseDown):
        """Prueba que se inicie el arrastre."""
        self.controller.start_drag()
        mock_mouseDown.assert_called_once()
        self.assertTrue(self.controller.is_dragging)

    @patch('pyautogui.mouseUp')
    def test_release_drag(self, mock_mouseUp):
        """Prueba que se suelte el arrastre."""
        self.controller.is_dragging = True
        self.controller.release_drag()
        mock_mouseUp.assert_called_once()
        self.assertFalse(self.controller.is_dragging)

    @patch('pyautogui.scroll')
    def test_scroll_up(self, mock_scroll):
        """Prueba el scroll hacia arriba."""
        self.controller.scroll_up()
        mock_scroll.assert_called_once_with(self.controller.scroll_amount)

    @patch('pyautogui.scroll')
    def test_scroll_down(self, mock_scroll):
        """Prueba el scroll hacia abajo."""
        self.controller.scroll_down()
        mock_scroll.assert_called_once_with(-self.controller.scroll_amount)

    @patch('pyautogui.moveTo')
    def test_move_cursor(self, mock_moveTo):
        """Prueba el movimiento del cursor."""
        self.controller.move_cursor(100, 200)
        mock_moveTo.assert_called_once_with(100, 200)

if __name__ == '__main__':
    unittest.main()
