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

REM === Set paths ===
set "CONTROLLER_DIR=%~dp0s"
set "PYTHON_DIR=%CONTROLLER_DIR%\python-embed\%ARCH%"
set "PYTHON_EXE=%PYTHON_DIR%\python.exe"
set "WEB_PY=%CONTROLLER_DIR%\web.py"

echo Using Python from: %PYTHON_EXE%

if not exist "%PYTHON_EXE%" (
    echo ❌ python.exe not found in: %PYTHON_DIR%
    pause
    exit /b 1
)

if not exist "%WEB_PY%" (
    echo ❌ web.py not found in: %CONTROLLER_DIR%
    pause
    exit /b 1
)

REM === Launch web.py ===
echo ✅ Launching web.py...
start "" "%PYTHON_EXE%" "%WEB_PY%"

pause
exit