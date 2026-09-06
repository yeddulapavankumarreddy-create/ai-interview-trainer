@echo off
REM ============================================================
REM AI Interview Trainer — Quick Start Script (Windows)
REM ============================================================

echo.
echo  AI Interview Trainer Agent - Quick Start
echo  Problem Statement No. 22 - IBM Granite / watsonx.ai
echo  ============================================================
echo.

REM --- Backend ---
echo [1/2] Starting Backend...
echo.
echo   Make sure you have Python 3.9+ installed.
echo   To install dependencies: cd backend ^&^& pip install -r requirements.txt
echo.
echo   Starting backend on http://localhost:8000
echo   API docs available at: http://localhost:8000/docs
echo.

start cmd /k "cd backend && venv\Scripts\activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak > nul

REM --- Frontend ---
echo [2/2] Starting Frontend...
echo.
echo   Make sure you have Node.js 18+ installed.
echo   To install dependencies: cd frontend ^&^& npm install
echo.
echo   Starting frontend on http://localhost:5173
echo.

start cmd /k "cd frontend && npm run dev"

echo.
echo  ============================================================
echo  Both services are starting...
echo.
echo  Frontend: http://localhost:5173
echo  Backend:  http://localhost:8000
echo  API Docs: http://localhost:8000/docs
echo.
echo  Demo Mode is active by default.
echo  Add IBM credentials to backend/.env to enable IBM Granite.
echo  ============================================================
echo.
pause
