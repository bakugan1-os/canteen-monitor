import os
from pathlib import Path

# Джерело відео:
# - IP-камера: "rtsp://admin:admin@192.168.1.100:554/stream"
# - Файл для тестів: "test.mp4"
# - Raspberry Pi Camera Module (через V4L2): "/dev/video0" або "0"
VIDEO_SOURCE = os.getenv("VIDEO_SOURCE", str(Path(__file__).parent.parent / "test_real_people.jpg"))

# Пороги рівнів завантаженості
LEVEL_FREE = 0.40       # < 40% — зелений
LEVEL_BUSY = 0.80       # < 80% — синій
# >= 80% — червоний

# Частота оновлення WebSocket (сек)
WS_UPDATE_INTERVAL = 1.0

# Шлях до даних
DATA_DIR = Path(__file__).parent.parent / "data"
