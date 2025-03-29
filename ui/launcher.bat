@echo off
cd /d "%~dp0"

del "shutdown_flag.json" >nul 2>&1

REM === Detect architecture ===
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
set "CONTROLLER_DIR=%~dp0"
set "PYTHON_DIR=%CONTROLLER_DIR%\python-embed\%ARCH%"
set "PYTHON_EXE=%PYTHON_DIR%\python.exe"
set "WEB_PY=%CONTROLLER_DIR%\web.py"
set "BACKEND_PY=%CONTROLLER_DIR%\backend.py"
set "CHECK_VB_SETUP=%CONTROLLER_DIR%\check_vb_install.py"

REM === Validate files ===
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

if not exist "%BACKEND_PY%" (
    echo ❌ backend.py not found in: %CONTROLLER_DIR%
    pause
    exit /b 1
)

REM === Run VB-Audio Cable check ===
echo 🔍 Checking VB-Cable setup...
"%PYTHON_EXE%" "%CHECK_VB_SETUP%"
if errorlevel 1 (
    echo ⚠️  VB-Cable setup required. Exiting launcher.
    timeout /t 3 >nul
    exit /b
)

REM === Launch both scripts (no visible terminals) ===
start /B "" "%PYTHON_EXE%" "%WEB_PY%"
start /B "" "%PYTHON_EXE%" "%BACKEND_PY%"

exit