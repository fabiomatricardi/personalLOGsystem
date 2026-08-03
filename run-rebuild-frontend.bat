@echo off
setlocal enabledelayedexpansion

:: Ensure we run from the batch file's directory
cd /d "%~dp0"

echo ============================================
echo   Rebuild Frontend + Restart Backend
echo ============================================
echo.

:: ============================================
:: STEP 1: Rebuild frontend
:: ============================================
echo [1/2] Building frontend...
call npm run build --prefix frontend
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Frontend build failed
    pause
    exit /b 1
)
echo Frontend built successfully.
echo.

:: ============================================
:: STEP 2: Start backend
:: ============================================
echo [2/2] Starting backend server on port 8000...
echo.
echo   App: http://localhost:8000
echo.
echo Opening browser...
start http://localhost:8000
echo.
echo Press Ctrl+C to stop the server
echo.
call uv run python -m backend.main

pause
