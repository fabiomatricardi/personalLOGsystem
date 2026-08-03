@echo off
setlocal enabledelayedexpansion

:: Ensure we run from the batch file's directory
cd /d "%~dp0"

echo ============================================
echo   Dependency Check - Personal Log Manager
echo ============================================
echo.

set "ALL_OK=1"

:: ============================================
:: Check UV
:: ============================================
echo [1/4] Checking UV package manager...
where uv >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('uv --version') do set UV_VER=%%i
    echo   [OK] UV: !UV_VER!
) else (
    echo   [MISSING] UV is not installed
    set "ALL_OK=0"
)

:: ============================================
:: Check Python (managed by UV)
:: ============================================
echo.
echo [2/4] Checking Python (managed by UV)...
where uv >nul 2>&1
if %errorlevel% equ 0 (
    uv python list --only-installed 2>nul | findstr "3.12" >nul
    if !errorlevel! equ 0 (
        echo   [OK] Python 3.12: Installed via UV
    ) else (
        echo   [INFO] Python 3.12: Will be installed automatically by UV on first run
    )
) else (
    echo   [SKIP] Cannot check Python without UV
)

:: ============================================
:: Check Node.js
:: ============================================
echo.
echo [3/4] Checking Node.js...
where node >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('node --version') do set NODE_VER=%%i
    echo   [OK] Node.js: !NODE_VER!
) else (
    echo   [MISSING] Node.js is not installed
    set "ALL_OK=0"
)

:: ============================================
:: Check npm
:: ============================================
echo.
echo [4/4] Checking npm...
where npm >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('npm --version') do set NPM_VER=%%i
    echo   [OK] npm: !NPM_VER!
) else (
    echo   [MISSING] npm is not installed (comes with Node.js)
    set "ALL_OK=0"
)

:: ============================================
:: Summary
:: ============================================
echo.
echo ============================================
echo   Summary
echo ============================================
echo.
if "!ALL_OK!"=="1" (
    echo   All dependencies are installed!
    echo.
    echo   You can run:
    echo     - run-dev.bat     (for development)
    echo     - run-build.bat   (to build executable)
) else (
    echo   Some dependencies are missing.
    echo.
    echo   This application requires:
    echo     - UV           (auto-installed by run-dev.bat / run-build.bat)
    echo     - Python 3.12+ (auto-installed by UV)
    echo     - Node.js      (auto-installed by run-dev.bat / run-build.bat)
    echo     - npm          (comes with Node.js)
    echo.
    echo   All missing dependencies will be installed automatically
    echo   when you run run-dev.bat or run-build.bat
)
echo.
pause
