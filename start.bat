@echo off
echo Starting AI RAG System...
echo.

echo Starting Backend...
start "Backend" cmd /k "cd backend && python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak > nul

echo Starting Frontend...
start "Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo System started!
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
pause