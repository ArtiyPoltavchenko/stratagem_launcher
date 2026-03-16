@echo off
echo Building Stratagem Launcher...
cd /d "%~dp0\.."

if not exist ".venv_win\Scripts\activate.bat" (
    echo [ERROR] Windows venv not found. Run:
    echo   python -m venv .venv_win
    echo   .venv_win\Scripts\activate
    echo   pip install -r requirements.txt -r requirements-build.txt
    pause
    exit /b 1
)

call .venv_win\Scripts\activate.bat
pip install -r requirements-build.txt --quiet

pyinstaller ^
    --onefile ^
    --windowed ^
    --name "Stratagem Launcher" ^
    --add-data "data;data" ^
    --add-data "web;web" ^
    --add-data "server;server" ^
    desktop\server_manager.py

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed. See output above.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  Built: dist\Stratagem Launcher.exe
echo  Copy it anywhere and double-click to run.
echo  data/ and web/ are bundled inside the .exe.
echo ============================================================
pause
