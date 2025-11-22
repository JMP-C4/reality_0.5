"""Entry point for gesture_controller_v2 (GUI por defecto, CLI opcional)."""

import argparse
import signal
import sys
import time

from PySide6.QtWidgets import QApplication

from .components.main_window import MainWindow
from .controllers.gesture_controller import GestureController
from .utils.logger import get_logger

log = get_logger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description="Gesture Controller v2")
    parser.add_argument("--camera-index", type=int, default=0, help="Indice de camara (0/1/2).")
    parser.add_argument("--no-preview", action="store_true", help="Desactiva ventana de preview (solo CLI).")
    parser.add_argument("--cli", action="store_true", help="Ejecuta en modo CLI (sin Qt).")
    return parser.parse_args()


def run_cli(camera_index: int, preview: bool):
    controller = GestureController(camera_index=camera_index, preview=preview)

    def shutdown(signum=None, frame=None):
        log.info("Shutting down gesture loop.")
        controller.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    started = controller.start()
    if not started:
        log.error("No se pudo iniciar la camara. Revisa que no este en uso y prueba otro indice (0/1/2).")
        sys.exit(1)

    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        shutdown()


def run_gui(camera_index: int):
    app = QApplication(sys.argv)
    window = MainWindow(camera_index=camera_index)
    window.show()
    sys.exit(app.exec())


def main():
    args = parse_args()
    if args.cli:
        run_cli(camera_index=args.camera_index, preview=not args.no_preview)
    else:
        run_gui(camera_index=args.camera_index)


if __name__ == "__main__":
    main()
