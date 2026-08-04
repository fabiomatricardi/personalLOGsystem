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

:: Read port from config.json
set PORT=8000
if exist config.json (
    for /f "tokens=*" %%i in ('powershell -Command "(Get-Content config.json | ConvertFrom-Json).app.port"') do set PORT=%%i
)
if "%PORT%"=="" set PORT=8000

echo [2/2] Starting backend server on port %PORT%...
echo.
echo   App: http://localhost:%PORT%
echo.
echo Opening browser...
start http://localhost:%PORT%
echo.
echo Press Ctrl+C to stop the server
echo.
call uv run python -m backend.main

pause
