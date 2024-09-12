@echo off

timeout /t 1 /nobreak >nul

cd /d C:\Program Files (x86)\Microsoft\Edge\Application

start msedge.exe http://127.0.0.1:8000/dev/
