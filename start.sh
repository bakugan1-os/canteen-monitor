#!/bin/bash
PROJECT_DIR="$HOME/canteen-monitor"
BACKEND_DIR="$PROJECT_DIR/backend"
VENV_DIR="$PROJECT_DIR/.venv"

if pgrep -f "uvicorn main:app" > /dev/null; then
    echo "⚠️ Сервер вже запущено."
    exit 0
fi

source "$VENV_DIR/bin/activate"
mkdir -p "$PROJECT_DIR/logs"

echo "🚀 Запуск Canteen Monitor..."

cd "$BACKEND_DIR"
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > "$PROJECT_DIR/logs/server.log" 2>&1 &
echo "✅ Сервер запущено"

IP=$(hostname -I | awk '{print $1}')

echo ""
echo "📍 Доступ до дашборду:"
echo "   На Raspberry Pi:  http://localhost:8000"
echo "   В локальній мережі: http://$IP:8000"
echo ""
echo "📊 Аналітика: http://localhost:8000/analytics"
echo "🎥 Візуалізатор: python $BACKEND_DIR/visualizer.py"
echo "🛑 Зупинити: $PROJECT_DIR/stop.sh"