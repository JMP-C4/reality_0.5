# Reality Hologram (Pepper Ghost)

Borrador del modulo de render. Recibe comandos del gesture_controller y genera las cuatro vistas (front, back, left, right) para el layout en cruz usado en Pepper's Ghost.

Estructura base
- src/core: eventos comunes y pipeline central.
- src/controllers: capa de entrada para comandos externos.
- src/rendering: rig de camaras, composicion de vistas y renderer (Panda3D offscreen).
- src/services: registro de assets y utilidades de carga.
- src/scenes: definiciones de escenas o presets.
- assets/: deja aqui los modelos .glb/.gltf/.obj para el holograma. Por ahora los modelos viven en reality/assets y se pueden mover luego.
- tests/: carpeta para pruebas unitarias.

Notas rapidas
- Motor sugerido: Panda3D + panda3d-gltf para cargar .glb. `PepperRenderer` crea buffers offscreen por vista usando el rig de camaras.
- `services.model_registry` intenta leer primero `reality_hologram/assets` y si esta vacio busca una carpeta vecina `reality/assets`.
- `SceneManager.load(scene_id)` usa `scenes/catalog.py` para mapear un id a `asset_id` (por ej. `machinery` -> `excavator`) y devuelve metadata con ruta del modelo.
- Viewer rapido (onscreen): `python -m reality_hologram.src.viewer --scene excavator --spin`
