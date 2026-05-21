@echo off
title TanaProject Django Auto-Start
color 0A
cd /d "e:\Projects\TE"
:check_mysql
echo Waiting for MySQL port 3306...
netstat -an | find "LISTENING" | find ":3306" >nul 2>&1
if errorlevel 1 (
    timeout /t 5 /nobreak >nul
    goto check_mysql
)
echo Django starting on http://localhost:8000
python manage.py runserver 0.0.0.0:8000
:restart
echo Server stopped. Restart 10s...
timeout /t 10 /nobreak >nul
goto check_mysql
