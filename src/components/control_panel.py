"""
Panel de Control con Botones de Acción.
"""
from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QLabel

class ControlPanel(QWidget):
    """
    Panel con botones para controlar la aplicación.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()
        self.title_label = QLabel("Control Panel")
        self.btn_toggle_detection = QPushButton("Iniciar Detección")
        self.btn_exit = QPushButton("Salir")

        layout.addWidget(self.title_label)
        layout.addWidget(self.btn_toggle_detection)
        layout.addWidget(self.btn_exit)
        layout.addStretch()

        self.setLayout(layout)

        # Conectar señales
        self.btn_exit.clicked.connect(parent.close)
