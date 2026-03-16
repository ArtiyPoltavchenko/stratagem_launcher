@echo off
echo ========================================
echo  Stratagem Launcher - Server (localhost)
echo ========================================
echo.

cd /d "%~dp0\.."

if not exist ".venv_win\Scripts\activate.bat" (
    echo [ERROR] Windows venv not found. Run this first:
    echo   python -m venv .venv_win
    echo   .venv_win\Scripts\activate
    echo   pip install -r requirements.txt
    pause
    exit /b 1
)

call .venv_win\Scripts\activate.bat
echo [OK] Virtual environment activated
echo [..] Starting server on http://127.0.0.1:5000
echo [..] Press Ctrl+C to stop
echo.
python -m server.app
pause
