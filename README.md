# Canteen Monitor

Система моніторингу завантаженості черги у їдальні.

## Структура проєкту

- `backend/` — FastAPI + WebSocket сервер, детектор, камера
- `frontend/` — веб-дашборд (HTML + JS)
- `tools/` — утиліти (наприклад, ROI-конфігуратор)
- `data/` — дані (ROI, статистика)

## Швидкий старт

### 1. Віртуальне оточення (обов'язково!)

```bash
cd canteen-monitor
python3 -m venv .venv
source .venv/bin/activate
```

> На Raspberry Pi ніколи не ставте залежності в системний Python.

### 2. Залежності

```bash
pip install -r requirements.txt
```

> На Raspberry Pi 5 це займе 10–20 хвилин (torch ~600 МБ). Не переривайте.

### 3. Запуск (на Raspberry Pi)

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

> `--reload` не використовуйте на Pi — зайве навантаження на CPU.

Відкрий `http://[IP-адреса-Pi]:8000/` у браузері на будь-якому пристрої в тій же мережі.

### 4. Автозапуск (опціонально, після налаштування)

```bash
sudo systemctl enable --now canteen-monitor
```

