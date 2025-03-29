@echo off
cd /d "%~dp0"

REM === Detect system architecture ===
set "ARCH="
set "PROCESSOR=%PROCESSOR_ARCHITECTURE%"

echo Detected architecture: %PROCESSOR%

if /i "%PROCESSOR%"=="AMD64" (
    set "ARCH=64-bit (AMD64)"
) else if /i "%PROCESSOR%"=="x86" (
    set "ARCH=32-bit (x86)"
) else if /i "%PROCESSOR%"=="ARM64" (
    set "ARCH=ARM64"
) else (
    echo ❌ Unknown architecture: %PROCESSOR%
    pause
    exit /b 1
)

echo ✅ System architecture detected as: %ARCH%

pause
exit