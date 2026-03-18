@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0\.."
title Stratagem Launcher — Build

:: Read version from _version.py
set VERSION=unknown
for /f "tokens=2 delims==" %%v in ('python -c "from _version import __version__; print(__version__)" 2^>nul') do set VERSION=%%v
if "!VERSION!"=="unknown" (
    for /f "tokens=2 delims==" %%v in ('findstr "__version__" _version.py') do (
        set RAW=%%v
        set RAW=!RAW: =!
        set VERSION=!RAW:"=!
    )
)
set EXE_NAME=Stratagem Launcher v!VERSION!

cls
echo.
echo  ^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=
echo       STRATAGEM LAUNCHER  --  BUILD SCRIPT  ^|  Version !VERSION!
echo  ^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=
echo.

echo  [ 1 / 6 ]  Checking Python...
where python >nul 2>&1
if errorlevel 1 (
    echo  [FAIL]  Python not found in PATH.
    echo          Install from https://python.org  (check "Add Python to PATH"^)
    pause & exit /b 1
)
for /f "tokens=*" %%v in ('python -c "import sys; print(sys.version_info.major, sys.version_info.minor)"') do set PYVER=%%v
for /f "tokens=1" %%a in ("!PYVER!") do set PYMAJ=%%a
for /f "tokens=2" %%b in ("!PYVER!") do set PYMIN=%%b
if !PYMAJ! LSS 3 goto :badpython
if !PYMAJ! EQU 3 if !PYMIN! LSS 10 goto :badpython
goto :goodpython
:badpython
echo  [FAIL]  Python 3.10+ required. Found !PYMAJ!.!PYMIN!
pause & exit /b 1
:goodpython
echo  [ OK ]  Python !PYMAJ!.!PYMIN!
echo.

echo  [ 2 / 6 ]  Setting up virtual environment...
if not exist ".venv_win\Scripts\activate.bat" (
    python -m venv .venv_win
    if errorlevel 1 ( echo  [FAIL]  Could not create venv. & pause & exit /b 1 )
    echo  [ OK ]  Created .venv_win
) else (
    echo  [ OK ]  .venv_win already exists, skipping.
)
echo.

echo  [ 3 / 6 ]  Activating environment and upgrading pip...
call .venv_win\Scripts\activate.bat
python -m pip install --upgrade pip --quiet
echo  [ OK ]  pip up to date.
echo.

echo  [ 4 / 6 ]  Installing runtime dependencies (requirements.txt)...
pip install -r requirements.txt --quiet
if errorlevel 1 ( echo  [FAIL]  requirements.txt failed. & pause & exit /b 1 )
echo  [ OK ]  flask, pynput, qrcode and others installed.
echo.

echo  [ 5 / 6 ]  Installing build dependencies (requirements-build.txt)...
pip install -r requirements-build.txt --quiet
if errorlevel 1 ( echo  [FAIL]  requirements-build.txt failed. & pause & exit /b 1 )
echo  [ OK ]  PyInstaller installed.
echo.

echo  [ 6 / 6 ]  Building executable...
echo             Output name: "!EXE_NAME!.exe"
echo.
if exist "dist\!EXE_NAME!.exe" del /f /q "dist\!EXE_NAME!.exe"
if exist "build" rmdir /s /q build

pyinstaller ^
    --onefile ^
    --windowed ^
    --name "!EXE_NAME!" ^
    --add-data "data;data" ^
    --add-data "web;web" ^
    --add-data "server;server" ^
    --add-data "_version.py;." ^
    --collect-all qrcode ^
    desktop\server_manager.py

if errorlevel 1 (
    echo.
    echo  [FAIL]  PyInstaller failed -- see output above.
    pause & exit /b 1
)

echo.
echo  ^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=
echo   BUILD SUCCESSFUL
echo.
echo   Output:  dist\!EXE_NAME!.exe
echo.
echo   The .exe is fully self-contained.
echo   Copy it anywhere and double-click -- no Python needed.
echo  ^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=
echo.
pause