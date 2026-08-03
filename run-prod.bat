@echo off
setlocal enabledelayedexpansion

:: Ensure we run from the batch file's directory
cd /d "%~dp0"

echo ============================================
echo   Personal Log Manager - Production Mode
echo ============================================
echo.

:: Check if executable exists
if not exist "dist\PersonalLogManager.exe" (
    echo ERROR: PersonalLogManager.exe not found in dist folder.
    echo Please run run-build.bat first to build the executable.
    pause
    exit /b 1
)

echo Starting Personal Log Manager...
echo.

:: Launch the executable
start "" "dist\PersonalLogManager.exe"

echo Application launched!
echo.
echo The application will open in your default browser.
echo Close this window or press Ctrl+C to exit.
echo.
pause
