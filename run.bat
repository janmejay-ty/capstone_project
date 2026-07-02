~@echo off
echo Starting ResolveDesk AI Services...

:: Start FastAPI backend
echo Launching backend API on http://localhost:8000 ...
start "ResolveDesk Backend" cmd /k "call "%~dp0venv\Scripts\activate.bat" && cd /d "%~dp0" && python -m uvicorn backend.app.main:app --reload --port 8000"

:: Start React frontend
echo Launching frontend dev server on http://localhost:5173 ...
start "ResolveDesk Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo Services started! Keep these terminal windows open.
pause
