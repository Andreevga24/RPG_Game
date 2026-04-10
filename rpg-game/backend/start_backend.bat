@echo off
cd /d "%~dp0"
echo RPG API: http://127.0.0.1:8000  (docs: /docs)
echo Остановка: Ctrl+C
py -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
pause
