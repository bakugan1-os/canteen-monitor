#!/bin/bash

PROJECT_DIR="$HOME/canteen-monitor"
BACKEND_DIR="$PROJECT_DIR/backend"
VENV_DIR="$PROJECT_DIR/.venv"

# Активуємо середовище
source "$VENV_DIR/bin/activate"

# Створюємо папку для логів
mkdir -p "$PROJECT_DIR/logs"

echo "🚀 Запуск Canteen Monitor..."

# 1. Сервер (бекенд + дашборд)
if ! pgrep -f "uvicorn main:app" > /dev/null; then
    cd "$BACKEND_DIR"
    nohup uvicorn main:app --host 0.0.0.0 --port 8000 > "$PROJECT_DIR/logs/server.log" 2>&1 &
    echo "📡 Сервер: http://0.0.0.0:8000"
else
    echo "⚠️ Сервер вже запущено"
fi

# 2. Візуалізатор (тільки якщо є монітор / графічна сесія)
if [ -n "$DISPLAY" ]; then
    if ! pgrep -f "visualizer.py" > /dev/null; then
        export DISPLAY=:0
        nohup python "$BACKEND_DIR/visualizer.py" > "$PROJECT_DIR/logs/visualizer.log" 2>&1 &
        echo "🎥 Візуалізатор запущено"
    else
        echo "⚠️ Візуалізатор вже запущено"
    fi
else
    echo "ℹ️ Візуалізатор пропущено (немає DISPLAY)"
fi

echo "📋 Дашборд: http://localhost:8000"
echo "🛑 Зупинити: $PROJECT_DIR/stop.sh"
echo "📊 Логи: $PROJECT_DIR/logs/"