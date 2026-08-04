@echo off
setlocal enabledelayedexpansion

:: Ensure we run from the batch file's directory
cd /d "%~dp0"

echo ============================================
echo   Personal Log Manager - Dev Mode
echo ============================================
echo.

:: ============================================
:: STEP 1: Check and Install UV
:: ============================================
echo [1/4] Checking UV package manager...
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo UV is not installed. Installing UV...
    echo This requires administrator privileges.
    echo.
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    if !errorlevel! neq 0 (
        echo.
        echo ERROR: Failed to install UV
        echo Please install manually from: https://github.com/astral-sh/uv
        pause
        exit /b 1
    )
    echo.
    echo UV installed successfully!
    echo Refreshing PATH...
    set "PATH=%USERPROFILE%\.local\bin;%PATH%"
)

:: Verify UV is working
uv --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ERROR: UV is installed but not working properly.
    echo Please restart this script or your terminal.
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('uv --version') do set UV_VER=%%i
echo UV found: !UV_VER!

:: ============================================
:: STEP 2: Check and Install Node.js
:: ============================================
echo.
echo [2/4] Checking Node.js...
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo Node.js is not installed. Installing Node.js...
    echo.
    where winget >nul 2>&1
    if !errorlevel! equ 0 (
        echo Using winget to install Node.js LTS...
        winget install -e --id OpenJS.NodeJS.LTS --accept-package-agreements --accept-source-agreements
        if !errorlevel! neq 0 (
            echo.
            echo ERROR: Failed to install Node.js via winget
            echo Please install manually from: https://nodejs.org/
            echo.
            start https://nodejs.org/
            pause
            exit /b 1
        )
        echo.
        echo Node.js installed successfully!
        echo Refreshing environment...
        for /f "usebackq tokens=2*" %%A in (`reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path 2^>nul`) do set "SYS_PATH=%%B"
        for /f "usebackq tokens=2*" %%A in (`reg query "HKCU\Environment" /v Path 2^>nul`) do set "USR_PATH=%%B"
        set "PATH=!SYS_PATH!;!USR_PATH!"
        if exist "%ProgramFiles%\nodejs" set "PATH=%ProgramFiles%\nodejs;!PATH!"
        if exist "%ProgramFiles(x86)%\nodejs" set "PATH=%ProgramFiles(x86)%\nodejs;!PATH!"
    ) else (
        echo.
        echo ERROR: Node.js not found and winget is not available.
        echo.
        echo Please install Node.js manually:
        echo   1. Go to https://nodejs.org/
        echo   2. Download and install the LTS version
        echo   3. Restart this script after installation
        echo.
        start https://nodejs.org/
        pause
        exit /b 1
    )
)

:: Verify Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Node.js is installed but not working properly.
    echo Please restart this script or your terminal.
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('node --version') do set NODE_VER=%%i
echo Node.js found: !NODE_VER!
for /f "tokens=*" %%i in ('npm --version') do set NPM_VER=%%i
echo npm found: !NPM_VER!

:: ============================================
:: STEP 3: Install Python dependencies via UV
:: ============================================
echo.
echo [3/4] Installing Python dependencies...
echo UV will automatically download Python 3.12 if not present.
echo.
call uv sync
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to install Python dependencies
    pause
    exit /b 1
)

:: ============================================
:: STEP 4: Install frontend dependencies
:: ============================================
echo.
echo [4/4] Installing frontend dependencies...
call npm install --prefix frontend
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to install frontend dependencies
    pause
    exit /b 1
)

:: ============================================
:: START APPLICATION
:: ============================================
echo.
echo ============================================
echo   All dependencies installed successfully!
echo ============================================
echo.

:: Read port from config.json
set PORT=8000
if exist config.json (
    for /f "tokens=*" %%i in ('powershell -Command "(Get-Content config.json | ConvertFrom-Json).app.port"') do set PORT=%%i
)
if "%PORT%"=="" set PORT=8000

:: Start Vite dev server in background
echo Starting Vite dev server on port 5173...
start "Vite Dev Server" cmd /c "cd frontend && npx vite --port 5173"

:: Give Vite a moment to start
timeout /t 3 /nobreak >nul

:: Start backend in foreground
echo Starting backend server on port %PORT%...
echo   Frontend: http://localhost:5173
echo   Backend:  http://localhost:%PORT%
echo.
echo Opening browser...
start http://localhost:5173
echo.
echo Press Ctrl+C to stop the server
echo.
call uv run python -m backend.main

pause
