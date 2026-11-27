#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "=================================================="
echo "    NeuroScreen AI - Screening Support System    "
echo "=================================================="

# Check and clear conflicting processes if needed
if lsof -ti :8000 >/dev/null 2>&1; then
    echo "[!] Freeing Port 8000..."
    kill -9 $(lsof -ti :8000) 2>/dev/null || true
    sleep 1
fi

if lsof -ti :5173 >/dev/null 2>&1; then
    echo "[!] Freeing Port 5173..."
    kill -9 $(lsof -ti :5173) 2>/dev/null || true
    sleep 1
fi

echo "[1/2] Launching FastAPI Backend (http://127.0.0.1:8000)..."
source backend/venv/bin/activate
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!

sleep 2

echo "[2/2] Launching Vite Frontend (http://localhost:5173)..."
cd frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "NeuroScreen AI is live!"
echo "-> Frontend: http://localhost:5173"
echo "-> Backend:  http://127.0.0.1:8000"
echo "-> Press Ctrl+C anytime to stop both servers."
echo "=================================================="

cleanup() {
    echo ""
    echo "[*] Stopping NeuroScreen AI servers..."
    kill -9 $BACKEND_PID 2>/dev/null || true
    kill -9 $FRONTEND_PID 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

wait

