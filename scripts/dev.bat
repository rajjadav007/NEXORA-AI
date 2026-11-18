@echo off
echo Starting Nexora AI Development Environment...

if "%1"=="backend" (
    cd backend
    uvicorn app.main:app --reload --port 8000
) else if "%1"=="frontend" (
    cd frontend
    npm run dev
) else (
    echo Usage: scripts\dev.bat [frontend^|backend]
)
