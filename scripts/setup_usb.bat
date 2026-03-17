@echo off
:: Uses ADB_PATH env var if set (passed by server_manager.py), else falls back to system adb
if defined ADB_PATH (
    set ADB="%ADB_PATH%"
) else (
    set ADB=adb
)

echo ========================================
echo  Stratagem Launcher - USB (ADB) Setup
echo ========================================
echo.
echo This script forwards port 5000 from your phone to localhost.
echo Requires: phone connected with USB debugging enabled.
echo.
echo Running: %ADB% reverse tcp:5000 tcp:5000

%ADB% reverse tcp:5000 tcp:5000

if %errorlevel%==0 (
    echo.
    echo [OK] ADB port forwarding set up.
    echo [..] Open http://localhost:5000 on your phone's Chrome browser.
    echo [..] Keep this USB connection active while playing.
) else (
    echo.
    echo [ERROR] ADB failed. Make sure:
    echo   1. Android phone is connected via USB
    echo   2. USB debugging is enabled on phone
    echo   3. ADB is installed (use 'Install ADB' button in the app)
)
echo.
pause
