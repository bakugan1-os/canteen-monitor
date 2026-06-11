"""
Тестовий скрипт для перевірки детектора та ROI.

Використання:
    python test_detector.py photo.jpg
    python test_detector.py video.mp4
    python test_detector.py              # згенерує тестове фото
"""
import sys
import cv2
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))
from detector import detect_people
from zone import load_roi, is_inside


def create_test_image():
    img = np.ones((480, 640, 3), dtype=np.uint8) * 200
    people = [(100, 150, 180, 380), (250, 160, 330, 390), (420, 140, 520, 400)]
    for x1, y1, x2, y2 in people:
        cv2.rectangle(img, (x1, y1), (x2, y2), (30, 30, 30), -1)
        cv2.circle(img, ((x1 + x2) // 2, y1 - 10), 25, (30, 30, 30), -1)
    path = Path("test_image.jpg")
    cv2.imwrite(str(path), img)
    print(f"✅ Створено тестове зображення: {path}")
    return str(path)


def draw_roi(frame, roi, color=(255, 0, 0)):
    if len(roi) >= 3:
        pts = np.array(roi, dtype=np.int32).reshape((-1, 1, 2))
        cv2.polylines(frame, [pts], True, color, 2)


def test_on_image(path: str):
    frame = cv2.imread(path)
    if frame is None:
        print(f"❌ Не вдалося відкрити: {path}")
        return

    boxes = detect_people(frame)
    roi = load_roi()
    count_total = len(boxes)
    count_in_roi = 0

    draw_roi(frame, roi)

    for box in boxes:
        x1, y1, x2, y2, conf = box
        in_roi = is_inside(box, roi) if roi else True
        color = (0, 255, 0) if in_roi else (0, 0, 255)
        if in_roi:
            count_in_roi += 1
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        label = f"{conf:.2f}"
        cv2.putText(frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

    cv2.putText(frame, f"Total: {count_total}  |  In ROI: {count_in_roi}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    print(f"🔍 Знайдено людей: {count_total}")
    print(f"📊 В зоні ROI: {count_in_roi}")

    cv2.imshow("Detection + ROI", frame)
    print("Натисни будь-яку клавішу, щоб закрити...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def test_on_video(path: str):
    cap = cv2.VideoCapture(path)
    roi = load_roi()
    print(f"▶️ Відтворення: {path}  |  Натисни 'q' або ESC, щоб вийти.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        boxes = detect_people(frame)
        draw_roi(frame, roi)
        count_in_roi = sum(1 for b in boxes if (is_inside(b, roi) if roi else True))

        for box in boxes:
            x1, y1, x2, y2, conf = box
            in_roi = is_inside(box, roi) if roi else True
            color = (0, 255, 0) if in_roi else (0, 0, 255)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

        cv2.putText(frame, f"In ROI: {count_in_roi}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow("Video Detection + ROI", frame)
        if cv2.waitKey(1) & 0xFF in (27, ord('q')):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        source = sys.argv[1]
        if source.endswith(('.mp4', '.avi', '.mkv', '.mov')):
            test_on_video(source)
        else:
            test_on_image(source)
    else:
        img_path = create_test_image()
        test_on_image(img_path)
