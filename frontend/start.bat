@echo off
chcp 65001 >nul
echo ========================================
echo   AI Chat Assistant - Frontend Server
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python first.
    pause
    exit /b 1
)

echo [INFO] Starting HTTP server...
echo [INFO] Please visit: http://localhost:8080 in your browser
echo [INFO] Press Ctrl+C to stop the server
echo.

cd /d "%~dp0"
python -m http.server 8080

pause