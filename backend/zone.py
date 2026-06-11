import json
import cv2
import numpy as np
from pathlib import Path

ROI_PATH = Path(__file__).parent.parent / "data" / "roi.json"

def save_roi(points: list):
    """Зберегти полігон ROI у JSON."""
    ROI_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(ROI_PATH, "w") as f:
        json.dump(points, f)

def load_roi() -> list:
    """Завантажити ROI. Повертає список [(x,y), ...]."""
    if not ROI_PATH.exists():
        return []
    with open(ROI_PATH) as f:
        return json.load(f)

def is_inside(box: list, polygon: list) -> bool:
    """
    Перевіряє, чи центр bounding box знаходиться всередині полігону.
    box: [x1, y1, x2, y2, conf]
    """
    x1, y1, x2, y2, _ = box
    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
    pts = np.array(polygon, dtype=np.int32)
    return cv2.pointPolygonTest(pts, (cx, cy), False) >= 0
