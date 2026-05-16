#!/bin/bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "======================================"
echo "   PaperTrail — Local Document AI    "
echo "======================================"

# Install dependencies if needed
if ! python -c "import fastapi" 2>/dev/null; then
  echo "[1/3] Installing dependencies..."
  pip install -r requirements.txt
fi

# Create data directories
mkdir -p data/uploads data/db

# Free ports if already in use
for PORT in 8000 7860; do
  PID=$(lsof -ti tcp:$PORT 2>/dev/null) && kill $PID 2>/dev/null && echo "      Freed port $PORT" || true
done
sleep 1

# Start FastAPI backend in background
echo "[2/3] Starting backend (FastAPI) on http://localhost:8000 ..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait for backend to be ready
echo "      Waiting for backend..."
until curl -s http://localhost:8000/docs > /dev/null 2>&1; do sleep 1; done
echo "      Backend ready."

# Start Gradio frontend
echo "[3/3] Starting frontend (Gradio) on http://localhost:7860 ..."
python frontend/app.py &
FRONTEND_PID=$!

echo ""
echo "✅  PaperTrail is running!"
echo "   Frontend: http://localhost:7860"
echo "   API docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop."

# Cleanup on exit
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Stopped.'" EXIT
wait
