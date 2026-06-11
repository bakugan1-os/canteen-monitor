from ultralytics import YOLO
import cv2
import numpy as np

# Завантаження найлегшої моделі для CPU
model = YOLO("yolov8n.pt")

def detect_people(frame: np.ndarray) -> list:
    """
    Детектує людей на кадрі.
    Повертає список bounding boxes [x1, y1, x2, y2, conf].
    """
    results = model(frame, classes=[0], verbose=False)
    boxes = []
    for r in results:
        for box in r.boxes.data.cpu().numpy():
            x1, y1, x2, y2, conf, cls = box
            boxes.append([int(x1), int(y1), int(x2), int(y2), float(conf)])
    return boxes
