@echo off
setlocal enabledelayedexpansion

echo Detecting project directory...
set "PROJECT_DIR=%~dp0"
set "SCRIPT_PATH=%PROJECT_DIR%start_django_auto.bat"

echo Project dir: %PROJECT_DIR%
echo Script: %SCRIPT_PATH%

REM Delete old task
schtasks /delete /tn "TanaDjango" /f >nul 2>&1

REM Create new
schtasks /create /tn "TanaDjango" /tr "\"%SCRIPT_PATH%\"" /sc onlogon /rl highest /f

if %errorlevel% == 0 (
    echo.
    echo [SUCCESS] Startup task "TanaDjango" registered!
    echo Trigger: Logon, Run: %SCRIPT_PATH%
    echo.
    echo Test: Reboot PC.
) else (
    echo [FAILED] Run as Administrator.
)

pause

