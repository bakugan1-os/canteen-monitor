import asyncio
import threading
import time
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles

import detector
import zone
import stats
from camera import CameraSource
from config import VIDEO_SOURCE, LEVEL_FREE, LEVEL_BUSY, WS_UPDATE_INTERVAL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Thread-safe стан
state_lock = threading.Lock()
state = {
    "people_total": 0,
    "people_in_roi": 0,
    "max_people": 0,
    "level": "free",
    "percent": 0,
}

camera_source = None
running = False
processing_thread = None


def processing_loop():
    """Фоновий потік: читання кадрів → детекція → ROI → рівень."""
    global running
    while running:
        frame = camera_source.read()
        if frame is None:
            time.sleep(0.2)
            continue

        boxes = detector.detect_people(frame)
        roi = zone.load_roi()
        total = len(boxes)
        in_roi = sum(1 for b in boxes if zone.is_inside(b, roi)) if roi else total

        with state_lock:
            state["people_total"] = total
            state["people_in_roi"] = in_roi

            # Динамічна калібрація максимуму (пік за день)
            if in_roi > state["max_people"]:
                state["max_people"] = in_roi
                stats.save_max(state["max_people"])

            # Рівень завантаженості
            max_p = state["max_people"] if state["max_people"] > 0 else 1
            p = in_roi / max_p
            state["percent"] = int(p * 100)

            if p < LEVEL_FREE:
                state["level"] = "free"
            elif p < LEVEL_BUSY:
                state["level"] = "busy"
            else:
                state["level"] = "full"

        time.sleep(0.5)  # ~2 FPS обробки


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Запуск і зупинка фонових потоків."""
    global running, camera_source, processing_thread
    logger.info("🚀 Запуск системи...")

    state["max_people"] = stats.load_max()
    logger.info(f"📊 Завантажено max_people: {state['max_people']}")

    camera_source = CameraSource(VIDEO_SOURCE)
    camera_source.start()
    running = True

    processing_thread = threading.Thread(target=processing_loop, daemon=True)
    processing_thread.start()

    yield

    logger.info("🛑 Зупинка системи...")
    running = False
    camera_source.stop()


app = FastAPI(title="Canteen Monitor", lifespan=lifespan)


@app.get("/status")
async def get_status():
    """REST: поточний стан у JSON."""
    with state_lock:
        return {
            "people_total": state["people_total"],
            "people_in_roi": state["people_in_roi"],
            "max": state["max_people"],
            "level": state["level"],
            "percent": state["percent"],
        }


@app.post("/reset-max")
async def reset_max():
    """Скинути динамічний максимум."""
    with state_lock:
        state["max_people"] = 0
        stats.save_max(0)
    return {"message": "Максимум скинуто. Нова калібрація розпочнеться з нуля."}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket: real-time оновлення для дашборду."""
    await websocket.accept()
    try:
        while True:
            with state_lock:
                data = {
                    "people": state["people_in_roi"],
                    "max": state["max_people"],
                    "level": state["level"],
                    "percent": state["percent"],
                }
            await websocket.send_json(data)
            await asyncio.sleep(WS_UPDATE_INTERVAL)
    except Exception as e:
        logger.info(f"WebSocket disconnected: {e}")
    finally:
        await websocket.close()


# Роздаємо фронтенд як статичні файли
app.mount("/", StaticFiles(directory="../frontend", html=True), name="static")
