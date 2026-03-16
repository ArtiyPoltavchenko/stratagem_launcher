@echo off
echo ==========================================
echo  Stratagem Launcher - Server (WiFi mode)
echo ==========================================
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

REM Show local IP for convenience
echo.
echo Your local IP addresses:
powershell -Command "Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notmatch 'Loopback' -and $_.IPAddress -notmatch '^169' } | ForEach-Object { Write-Host ('  http://' + $_.IPAddress + ':5000') }"
echo.
echo Open one of these URLs on your phone's Chrome browser.
echo Press Ctrl+C to stop the server.
echo.

python -m server.app --host 0.0.0.0
pause
