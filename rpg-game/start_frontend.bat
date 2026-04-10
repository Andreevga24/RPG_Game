@echo off
cd /d "%~dp0"
echo Frontend: http://127.0.0.1:3001/pages/game.html
echo Остановка: Ctrl+C
py -m http.server 3001 --directory frontend
pause

