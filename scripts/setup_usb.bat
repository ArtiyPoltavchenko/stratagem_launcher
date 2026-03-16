@echo off
echo ========================================
echo  Stratagem Launcher - USB (ADB) Setup
echo ========================================
echo.
echo This script forwards port 5000 from your phone to localhost.
echo Requires: ADB installed and phone connected with USB debugging enabled.
echo.

adb reverse tcp:5000 tcp:5000

IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] ADB failed. Make sure:
    echo   1. Android phone is connected via USB
    echo   2. USB debugging is enabled on phone
    echo   3. ADB is installed and in PATH
    echo      Download: https://developer.android.com/studio/releases/platform-tools
    pause
    exit /b 1
)

echo.
echo [OK] Port forwarding active.
echo [..] Open http://localhost:5000 on your phone's Chrome browser.
echo [..] Keep this USB connection active while playing.
echo.
pause
