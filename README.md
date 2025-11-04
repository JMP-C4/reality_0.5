# Holographic Gesture Control

A Python application that uses computer vision to control the mouse with hand gestures.

## Features

*   Real-time hand tracking
*   Gesture recognition (pointing, click, drag, and drop)
*   Mouse control (move, click, drag)

## Dependencies

*   Python 3
*   OpenCV
*   MediaPipe
*   PySide6

## How to Run

1.  Install the dependencies: `pip install opencv-python mediapipe pyside6`
2.  Download the `hand_landmarker.task` file from [here](https://huggingface.co/lithiumice/models_hub/resolve/8a7b241f38e33d194a06f881a1211b3e7eda4edd/hand_landmarker.task) and place it in the root of the project.
3.  Run the application: `python -m src.main`
