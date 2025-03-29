@echo off
cd /d "%~dp0"

REM === Detect system architecture ===
set "ARCH="
set "PROCESSOR=%PROCESSOR_ARCHITECTURE%"

echo Detected architecture: %PROCESSOR%

if /i "%PROCESSOR%"=="AMD64" (
    set "ARCH=python-3.13.2-embed-amd64"
) else if /i "%PROCESSOR%"=="x86" (
    set "ARCH=python-3.13.2-embed-win32"
) else if /i "%PROCESSOR%"=="ARM64" (
    set "ARCH=python-3.13.2-embed-arm64"
) else (
    echo ❌ Unknown architecture: %PROCESSOR%
    pause
    exit /b 1
)

REM === Full path to embedded Python ===
set "PYTHON_DIR=%~dp0python-embed\%ARCH%"
set "PYTHON_EXE=%PYTHON_DIR%\python.exe"

echo Using Python from: %PYTHON_EXE%

if not exist "%PYTHON_EXE%" (
    echo ❌ python.exe not found in: %PYTHON_DIR%
    pause
    exit /b 1
)

REM === Set PYTHONPATH so Python can find libraries ===
set PYTHONPATH=%PYTHON_DIR%\Lib;%PYTHON_DIR%\Lib\site-packages

echo ✅ Launching web.py...
start "" "%PYTHON_EXE%" "%~dp0web.py"

timeout /t 1 >nul

echo ✅ Launching backend.py...
start "" "%PYTHON_EXE%" "%~dp0backend.py"

echo ✅ All launched. You can close this window.
pause
exit