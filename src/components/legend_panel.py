
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout

class LegendPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("<b>Legend:</b>"))
        layout.addWidget(QLabel("<b>Pointing:</b> Move cursor"))
        layout.addWidget(QLabel("<b>Click:</b> Left click"))
        layout.addWidget(QLabel("<b>Fist:</b> Start drag"))
        layout.addWidget(QLabel("<b>Open Hand:</b> Release drag"))
        self.setLayout(layout)
