@echo off

:: Ensure we run from the batch file's directory
cd /d "%~dp0"

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting Administrator privileges...
    powershell -Command "Start-Process cmd -ArgumentList '/c \"%~f0\" %*' -Verb RunAs"
    exit /b
)

echo ============================================
echo   Personal Log Manager - Windows Defender Exclusion
echo ============================================
echo.
echo This script adds a Windows Defender exclusion
echo so the Personal Log Manager exe is not blocked by
echo SmartScreen or antivirus.
echo.

set "APP_FOLDER=%~dp0"
if not "%~1"=="" set "APP_FOLDER=%~1"

echo Adding exclusion for: %APP_FOLDER%
powershell -Command "Add-MpPreference -ExclusionPath '%APP_FOLDER%'"

if %errorlevel% equ 0 (
    echo.
    echo SUCCESS: Exclusion added.
    echo The Personal Log Manager exe should no longer be blocked.
) else (
    echo.
    echo FAILED: Could not add exclusion.
    echo You may need to manually add the folder in Windows Security settings.
)

echo.
pause
