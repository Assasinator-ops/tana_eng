@echo off
title TanaProject Django - Auto after MySQL
color 0A

REM Change to project dir
cd /d "e:\Projects\TE"

echo [%date% %time%] Starting TanaProject auto-service...
echo Waiting for XAMPP MySQL (port 3306) - press Ctrl+C to stop.

:check_xampp
netstat -an ^| find "LISTENING" ^| find ":3306." >nul 2>&1
if errorlevel 1 (
    echo [%date% %time%] XAMPP not ready. Retrying in 5s...
    timeout /t 5 /nobreak >nul
    goto check_xampp
)

echo [%date% %time%] XAMPP ready! Running migrations...
python manage.py migrate --noinput

echo [%date% %time%] Starting Django dev server on http://0.0.0.0:8000
python manage.py runserver 0.0.0.0:8000

:restart_if_crashed
echo [%date% %time%] Server stopped. Restarting in 10s...
timeout /t 10 /nobreak >nul
goto check_xampp
