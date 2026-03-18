@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0\.."

echo.
echo  ============================================================
echo   Stratagem Launcher -- One-Click Build
echo  ============================================================
echo.

:: ── 1. Check Python ──────────────────────────────────────────
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found in PATH.
    echo.
    echo   Please install Python 3.10+ from https://python.org
    echo   Make sure to check "Add Python to PATH" during install.
    echo.
    pause & exit /b 1
)

for /f "tokens=*" %%v in ('python -c "import sys; print(sys.version_info.major, sys.version_info.minor)"') do set PYVER=%%v
for /f "tokens=1" %%a in ("!PYVER!") do set PYMAJ=%%a
for /f "tokens=2" %%b in ("!PYVER!") do set PYMIN=%%b

if !PYMAJ! LSS 3 (
    echo [ERROR] Python 3.10+ required. Found: !PYMAJ!.!PYMIN!
    pause & exit /b 1
)
if !PYMAJ! EQU 3 if !PYMIN! LSS 10 (
    echo [ERROR] Python 3.10+ required. Found: !PYMAJ!.!PYMIN!
    pause & exit /b 1
)

echo [OK] Python !PYMAJ!.!PYMIN! found.

:: ── 2. Create venv if missing ────────────────────────────────
if not exist ".venv_win\Scripts\activate.bat" (
    echo.
    echo [SETUP] Creating Windows virtual environment...
    python -m venv .venv_win
    if errorlevel 1 (
        echo [ERROR] Failed to create venv.
        pause & exit /b 1
    )
    echo [OK] Virtual environment created.
) else (
    echo [OK] Virtual environment already exists.
)

:: ── 3. Activate venv ─────────────────────────────────────────
call .venv_win\Scripts\activate.bat

:: ── 4. Upgrade pip silently ───────────────────────────────────
echo.
echo [SETUP] Upgrading pip...
python -m pip install --upgrade pip --quiet

:: ── 5. Install runtime dependencies ──────────────────────────
echo [SETUP] Installing runtime dependencies (requirements.txt)...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install requirements.txt
    pause & exit /b 1
)

:: ── 6. Install build dependencies ────────────────────────────
echo [SETUP] Installing build dependencies (requirements-build.txt)...
pip install -r requirements-build.txt --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install requirements-build.txt
    pause & exit /b 1
)

echo [OK] All dependencies installed.

:: ── 7. Clean previous build ──────────────────────────────────
echo.
echo [BUILD] Cleaning previous build artifacts...
if exist "dist\Stratagem Launcher.exe" del /f /q "dist\Stratagem Launcher.exe"
if exist "build" rmdir /s /q build

:: ── 8. Run PyInstaller ───────────────────────────────────────
echo [BUILD] Running PyInstaller...
echo.

pyinstaller ^
    --onefile ^
    --windowed ^
    --name "Stratagem Launcher" ^
    --add-data "data;data" ^
    --add-data "web;web" ^
    --add-data "server;server" ^
    --collect-all qrcode ^
    desktop\server_manager.py

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed. See output above.
    pause & exit /b 1
)

:: ── 9. Done ──────────────────────────────────────────────────
echo.
echo  ============================================================
echo   SUCCESS: dist\Stratagem Launcher.exe
echo.
echo   The .exe is fully self-contained.
echo   Copy it anywhere and double-click to run.
echo   No Python, no venv, no dependencies needed on target PC.
echo  ============================================================
echo.
pause