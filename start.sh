#!/bin/bash
# ============================================================
# AI Interview Trainer — Quick Start Script (Linux/macOS)
# ============================================================

echo ""
echo " AI Interview Trainer Agent - Quick Start"
echo " Problem Statement No. 22 - IBM Granite / watsonx.ai"
echo " ============================================================"
echo ""

# Backend
echo "[1/2] Starting Backend on http://localhost:8000..."
cd backend
if [ ! -d "venv" ]; then
  python3 -m venv venv
  echo "Virtual environment created."
fi
source venv/bin/activate
pip install -r requirements.txt -q
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

sleep 2

# Frontend
echo "[2/2] Starting Frontend on http://localhost:5173..."
cd frontend
if [ ! -d "node_modules" ]; then
  npm install
fi
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo " ============================================================"
echo " Frontend: http://localhost:5173"
echo " Backend:  http://localhost:8000"
echo " API Docs: http://localhost:8000/docs"
echo ""
echo " Demo Mode active. Add IBM credentials to backend/.env"
echo " ============================================================"
echo ""
echo "Press Ctrl+C to stop all services."

wait $BACKEND_PID $FRONTEND_PID
