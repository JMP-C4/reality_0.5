Estructura Base
gesture_controller/
│
├── src/
│   ├── components/         # Interfaz gráfica (PySide6)
│   ├── controllers/        # Controladores que ejecutan acciones
│   ├── services/           # Detección y análisis de gestos (MediaPipe)
│   ├── utils/              # Funciones auxiliares y herramientas
│   ├── core/               # (Opcional) Configuración y eventos compartidos
│   └── main.py             # Punto de entrada
│
├── tests/                  # Pruebas unitarias
└── assets/                 # Modelos, íconos, configuraciones 

⚙️ Diseño y Patrones de Software

El sistema sigue una arquitectura MVC mejorada, combinando tres patrones clave:

Capa	Patrón	Rol
components/	MVC – View	Interfaz Qt (paneles, cámara, botones)
controllers/	MVC – Controller / Observer	Maneja lógica y responde a gestos
services/	MVC – Model / Strategy	Detección de mano, mapeo de gestos, IA
utils/	Helper	Funciones de apoyo (logs, config, etc.)
core/	Facade / Singleton (opcional)	Punto central de estado global y eventos
🧩 Componentes Principales
🪟 components/

main_window.py → Ventana principal (video + paneles laterales)

control_panel.py → Botones de control (iniciar, calibrar, salir, etc.)

legend_panel.py → Leyenda o guía visual de gestos reconocidos

👉 Usa QHBoxLayout y QVBoxLayout para una interfaz modular y clara.

🎮 controllers/

gesture_controller.py → Traduce gestos detectados a acciones del sistema

(Futuro) system_controller.py, hologram_controller.py
👉 Aplica Observer para reaccionar a eventos de gestos.

🤖 services/

hand_tracking.py → Inicializa MediaPipe y procesa los landmarks de la mano

gesture_mapper.py → Asigna combinaciones de landmarks a gestos conocidos
👉 Aplica Strategy para intercambiar métodos de detección o IA.

🧠 utils/

logger.py → Sistema de logs

config_loader.py → Carga de configuraciones JSON/YAML

math_tools.py → Cálculos geométricos y de distancias

⚙️ core/ (opcional pero útil)

app_context.py → Mantiene estados compartidos (modo detección, calibración)

events.py → Define señales o eventos comunes entre módulos

👉 Facilita la conexión futura con el módulo reality_hologram.

🧩 Integración Planeada

El módulo gesture_controller funcionará de forma independiente, pero estará diseñado para enviar datos o señales hacia reality_hologram.

reality_hologram será el siguiente proyecto, responsable de mostrar la proyección visual 3D (Panda3D / OpenGL) según los gestos detectados.

🔁 Flujo General

Captura de video con OpenCV

Procesamiento de la mano (MediaPipe → landmarks)

Detección del gesto (GestureMapper)

Ejecución de acción (GestureController)

Retroalimentación visual en la UI (MainWindow)