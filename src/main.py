"""
Punto de Entrada Principal de la Aplicación de Control por Gestos.
"""
import sys
from PySide6.QtWidgets import QApplication
from src.components.main_window import MainWindow

def main():
    """
    Inicializa y ejecuta la aplicación.
    """
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
