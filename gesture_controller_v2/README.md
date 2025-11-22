# Gesture Controller v2

Version paralela para experimentar sin tocar el controlador original. Mantiene la arquitectura por modulos y se conecta al renderer (`reality_hologram`) via un `CommandBridge` minimal.

Estructura
- src/main.py: punto de entrada (GUI por defecto, CLI opcional con flags).
- src/components: interfaz Qt (`main_window.py`) similar a tu UI original.
- src/core: eventos y puente hacia reality_hologram.
- src/services: captura de camara, deteccion con MediaPipe y mapeo de gestos.
- src/controllers: orquestacion del loop de captura -> mapeo -> comandos.
- src/utils: logger simple.
- assets/: recursos opcionales (iconos, configs). No se usan en el loop base.
- tests/: espacio para pruebas.

Flujo
GUI:
1) `CameraWorker` (QThread) lee frames con OpenCV (DirectShow/MSMF fallback), dibuja landmarks y emite QImage.
2) `GestureMapper` traduce landmarks a eventos (open/fist/pinch/point).
3) `MainWindow` muestra la vista de camara, leyenda y ultimo gesto; envia comandos a `CommandBridge` -> `RealityPipeline`.

CLI (modo opcional con `--cli`):
1) `CameraLoop` lee frames.
2) `MediapipeHandTracker` + `GestureMapper`.
3) `GestureController` emite comandos al pipeline y loggea en consola.

Ejecucion rapida
- GUI: `python -m gesture_controller_v2.src.main`
- CLI: `python -m gesture_controller_v2.src.main --cli --no-preview`
- Boton "Abrir Holograma": lanza el viewer de `reality_hologram` en otra ventana (Panda3D, escena por defecto).

Notas
- Se reutilizan dependencias existentes (opencv-python, mediapipe, PySide6). No altera el `gesture_controller` original.
- El CLI imprime por consola los comandos generados y el resultado de pipeline.render_frame().
