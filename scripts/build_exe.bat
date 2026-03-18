@echo off
echo ============================================================
echo  Stratagem Launcher - Build Script
echo ============================================================
cd /d "%~dp0\.."

REM ---- 1. Check Python installation ----
python --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] Python not found. Attempting to install via winget...
    winget install --id Python.Python.3.11 --source winget --silent --accept-package-agreements --accept-source-agreements
    if errorlevel 1 (
        echo.
        echo [ERROR] winget install failed. Please install Python manually:
        echo   https://www.python.org/downloads/
        echo   Make sure to check "Add Python to PATH" during installation.
        pause
        exit /b 1
    )
    echo [INFO] Python installed. Refreshing PATH...
    REM Refresh PATH so python is available in this session
    for /f "tokens=*" %%i in ('where python 2^>nul') do set PYTHON_PATH=%%i
    if not defined PYTHON_PATH (
        echo [ERROR] Python still not found after install. Please restart and re-run this script.
        pause
        exit /b 1
    )
)

echo [OK] Python found:
python --version

REM ---- 2. Create venv if missing ----
if not exist ".venv_win\Scripts\activate.bat" (
    echo.
    echo [INFO] Virtual environment not found. Creating .venv_win...
    python -m venv .venv_win
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created.
)

REM ---- 3. Activate venv ----
echo.
echo [INFO] Activating virtual environment...
call .venv_win\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)
echo [OK] Virtual environment activated.

REM ---- 4. Upgrade pip ----
echo.
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip --quiet

REM ---- 5. Install dependencies ----
echo.
echo [INFO] Installing dependencies from requirements.txt...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install requirements.txt.
    pause
    exit /b 1
)

echo [INFO] Installing build dependencies from requirements-build.txt...
pip install -r requirements-build.txt --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install requirements-build.txt.
    pause
    exit /b 1
)
echo [OK] All dependencies installed.

REM ---- 6. Build exe ----
echo.
echo [INFO] Building executable with PyInstaller...
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "Stratagem Launcher" ^
    --add-data "data;data" ^
    --add-data "web;web" ^
    --add-data "server;server" ^
    --collect-all qrcode ^
    --collect-all flask ^
    --collect-all werkzeug ^
    --collect-all flask_cors ^
    --hidden-import flask ^
    --hidden-import werkzeug ^
    --hidden-import werkzeug.serving ^
    --hidden-import flask_cors ^
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
