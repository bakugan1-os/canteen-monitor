"""
Утиліта для малювання ROI-полігону на першому кадрі з камери.

Використання:
    python draw_roi.py

Кліки мишою — додати точку полігону.
Пробіл — зберегти ROI та вийти.
ESC — вийти без збереження.
"""
import cv2
import sys
import os
import numpy as np

# Додаємо backend у шлях, щоб імпортувати zone
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from zone import save_roi
from camera import CameraSource
from config import VIDEO_SOURCE

points = []
frame = None

source = VIDEO_SOURCE
if len(sys.argv) > 1:
    source = sys.argv[1]

cap = CameraSource(source)
cap.start()

# Зачекаємо перший кадр
import time
time.sleep(1)
frame = cap.read()
if frame is None:
    print("Не вдалося отримати кадр. Перевірте джерело:", source)
    sys.exit(1)

cap.stop()

def mouse_callback(event, x, y, flags, param):
    global points, frame
    if event == cv2.EVENT_LBUTTONDOWN:
        points.append([x, y])
        print(f"Точка додана: ({x}, {y})")
        redraw()

def redraw():
    img = frame.copy()
    if len(points) > 1:
        pts = np.array(points, dtype=np.int32).reshape((-1, 1, 2))
        cv2.polylines(img, [pts], False, (0, 255, 0), 2)
    for p in points:
        cv2.circle(img, tuple(p), 5, (0, 0, 255), -1)
    cv2.imshow("Draw ROI", img)

cv2.namedWindow("Draw ROI")
cv2.setMouseCallback("Draw ROI", mouse_callback)
redraw()

print("ЛКМ — додати точку. Пробіл — зберегти. ESC — вийти.")

while True:
    key = cv2.waitKey(0) & 0xFF
    if key == 27:  # ESC
        break
    if key == 32:  # Пробіл
        if len(points) >= 3:
            save_roi(points)
            print(f"ROI збережено: {points}")
        else:
            print("Потрібно мінімум 3 точки!")
        break

cv2.destroyAllWindows()
