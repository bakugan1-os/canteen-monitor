"""
Візуалізатор відео в реальному часі.
Показує кадр з камери, ROI, bounding boxes і статус черги.

Використання:
    cd backend
    python visualizer.py

Натисни 'q' або ESC для виходу.
"""
import sys
import cv2
import time
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from camera import CameraSource
from detector import detect_people
from zone import load_roi, is_inside
from stats import load_max, save_max
from config import VIDEO_SOURCE, LEVEL_FREE, LEVEL_BUSY


def main():
    roi = load_roi()
    max_people = load_max()

    print(f"🎥 Підключення до камери: {VIDEO_SOURCE}")
    camera = CameraSource(VIDEO_SOURCE)
    camera.start()

    # Чекаємо перший кадр (до 10 секунд)
    frame = None
    for _ in range(20):
        frame = camera.read()
        if frame is not None:
            break
        time.sleep(0.5)

    if frame is None:
        print("❌ Не вдалося отримати кадр з камери. Перевір URL у config.py")
        return

    print("✅ Візуалізатор запущено. Натисни 'q' або ESC для виходу.")

    while True:
        frame = camera.read()
        if frame is None:
            time.sleep(0.1)
            continue

        # Детекція
        boxes = detect_people(frame)
        total = len(boxes)
        in_roi = sum(1 for b in boxes if (is_inside(b, roi) if roi else True))

        # Динамічний max
        if in_roi > max_people:
            max_people = in_roi
            save_max(max_people)

        # Рівень і колір тексту (BGR)
        max_p = max_people if max_people > 0 else 1
        percent = in_roi / max_p
        if percent < LEVEL_FREE:
            level, color_text = "ВІЛЬНО", (0, 255, 0)       # Зелений
        elif percent < LEVEL_BUSY:
            level, color_text = "СЕРЕДНЯ", (255, 0, 0)      # Синій (BGR)
        else:
            level, color_text = "ПОВНА", (0, 0, 255)        # Червоний

        # Малювання ROI
        if len(roi) >= 3:
            pts = np.array(roi, dtype=np.int32).reshape((-1, 1, 2))
            cv2.polylines(frame, [pts], True, (255, 0, 255), 2)

        # Малювання bounding boxes
        for box in boxes:
            x1, y1, x2, y2, conf = box
            in_r = is_inside(box, roi) if roi else True
            color = (0, 255, 0) if in_r else (0, 0, 255)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            label = f"{conf:.2f}"
            cv2.putText(frame, label, (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        # Інфо-панель зверху
        h, w = frame.shape[:2]
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 50), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay, 0.6, frame, 0.4, 0)

        text = f"Queue: {in_roi}  |  Total: {total}  |  Max: {max_people}  |  {level} ({int(percent*100)}%)"
        cv2.putText(frame, text, (10, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color_text, 2)

        cv2.imshow("Canteen Monitor - Camera", frame)
        key = cv2.waitKey(1) & 0xFF
        if key in (27, ord('q')):
            break

    camera.stop()
    cv2.destroyAllWindows()
    print("🛑 Візуалізатор зупинено.")


if __name__ == "__main__":
    main()