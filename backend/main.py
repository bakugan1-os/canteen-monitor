import asyncio
import threading
import time
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

import detector
import zone
import stats
import analytics
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
    "last_log": 0,
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

            # Лог аналітики раз на 15 хвилин (900 секунд)
            if time.time() - state.get("last_log", 0) >= 900:
                analytics.log_state(state["people_in_roi"], state["level"])
                state["last_log"] = time.time()

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


@app.get("/analytics", response_class=HTMLResponse)
async def get_analytics():
    """HTML-звіт по 15-хвилинних слотах (11:30 – 14:00)."""
    report = analytics.get_report(days=7)
    
    html = """<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Аналітика черги</title>
    <style>
        body { font-family: Arial, sans-serif; background: #1a1a2e; color: #fff; padding: 20px; }
        h1 { text-align: center; font-weight: 300; }
        table { width: 100%; max-width: 700px; margin: 20px auto; border-collapse: collapse; }
        th, td { padding: 10px; border: 1px solid #444; text-align: center; }
        th { background: #16213e; }
        tr:nth-child(even) { background: #0f3460; }
        .green { color: #4ecca3; font-weight: bold; }
        .blue { color: #3498db; font-weight: bold; }
        .red { color: #e74c3c; font-weight: bold; }
        .info { text-align: center; color: #888; margin-top: 20px; }
        .back-link { display: block; text-align: center; margin-top: 20px; color: #4ecca3; text-decoration: none; }
        .back-link:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <h1>📊 Аналітика черги (11:30 – 14:00, останні 7 днів)</h1>
    <table>
        <tr>
            <th>Час</th>
            <th>Середня черга</th>
            <th>Записів</th>
            <th>% ПОВНА</th>
            <th>Рекомендація</th>
        </tr>
"""
    
    for row in report:
        color_class = ""
        if "Вільно" in row["recommend"]:
            color_class = "green"
        elif "Уникайте" in row["recommend"]:
            color_class = "red"
        elif "Завантажено" in row["recommend"] or "Помірно" in row["recommend"]:
            color_class = "blue"
        
        avg = f"{row['avg_people']:.1f}" if row["count"] > 0 else "—"
        pct = f"{row['pct_full']:.0f}%" if row["count"] > 0 else "—"
        
        html += f"""<tr>
            <td>{row['slot']}</td>
            <td>{avg}</td>
            <td>{row['count']}</td>
            <td>{pct}</td>
            <td class="{color_class}">{row['recommend']}</td>
        </tr>
"""
    
    html += """</table>
    <p class="info">Оновлюється автоматично. Дані записуються кожні 15 хвилин.</p>
    <a href="/" class="back-link">← Назад до дашборду</a>
</body>
</html>"""
    
    return HTMLResponse(content=html)


# Роздаємо фронтенд як статичні файли
app.mount("/", StaticFiles(directory="../frontend", html=True), name="static")
