#!/bin/bash
echo "🛑 Зупинка Canteen Monitor..."

pkill -f "uvicorn main:app"
pkill -f "visualizer.py"

echo "✅ Зупинено."