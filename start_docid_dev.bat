@echo off
cd /d "%~dp0"
echo ===== DOCiD: git pull =====
git pull
echo.
echo ===== Starting backend (Flask, port 5001) =====
start "DOCiD Backend" cmd /k "cd /d %~dp0backend && python run.py"
echo.
echo ===== Starting frontend (Next.js) =====
start "DOCiD Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"
echo.
echo Both servers launching in separate windows.
pause
