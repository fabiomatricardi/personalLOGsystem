@echo off
setlocal enabledelayedexpansion

:: Ensure we run from the batch file's directory
cd /d "%~dp0"

echo ============================================
echo   Personal Log Manager - Build
echo ============================================
echo.

:: ============================================
:: STEP 1: Check and Install UV
:: ============================================
echo [1/5] Checking UV package manager...
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

:: Verify UV
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
echo [2/5] Checking Node.js...
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo Node.js is not installed. Installing Node.js...
    where winget >nul 2>&1
    if !errorlevel! equ 0 (
        echo Using winget to install Node.js LTS...
        winget install -e --id OpenJS.NodeJS.LTS --accept-package-agreements --accept-source-agreements
        if !errorlevel! neq 0 (
            echo.
            echo ERROR: Failed to install Node.js via winget
            echo Please install manually from: https://nodejs.org/
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
        echo Please install Node.js from: https://nodejs.org/
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

:: ============================================
:: STEP 3: Install Python dependencies
:: ============================================
echo.
echo [3/5] Installing Python dependencies...
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
:: STEP 4: Clean previous builds
:: ============================================
echo.
echo [4/5] Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo Done.

:: ============================================
:: STEP 5: Build executable
:: ============================================
echo.
echo [5/5] Building executable...
call uv run python build.py
set BUILD_EXIT=!errorlevel!

:: Re-navigate to project root
cd /d "%~dp0"

:: Check if executable was created
if exist "dist\PersonalLogManager.exe" (
    echo.
    echo ============================================
    echo   BUILD SUCCESSFUL!
    echo ============================================
    echo.
    echo Executable: dist\PersonalLogManager.exe
    echo.
    echo The executable is STANDALONE and does NOT require:
    echo   - Python installed
    echo   - UV installed
    echo   - Node.js installed
    echo   - Any other dependencies
    echo.
    echo Deployment steps:
    echo   1. Run exclude-defender.bat - right-click, Run as Admin
    echo   2. Copy dist\PersonalLogManager.exe to target directory
    echo   3. Launch PersonalLogManager.exe
) else (
    echo.
    echo ============================================
    echo   BUILD FAILED
    echo ============================================
    echo.
    echo The executable was not created.
    echo Check the error messages above for details.
)

pause
