@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo   🛠️  Downloading + Extracting Wheels for win32 + ARM64
echo ========================================================

REM Set base paths
set "BASE_DIR=%~dp0"
set "WIN32_WHLS=%BASE_DIR%win32_packages"
set "ARM64_WHLS=%BASE_DIR%arm64_packages"

set "WIN32_SITEPKG=%BASE_DIR%controller\python-embed\python-3.13.2-embed-win32\Lib\site-packages"
set "ARM64_SITEPKG=%BASE_DIR%controller\python-embed\python-3.13.2-embed-arm64\Lib\site-packages"

REM Create folders if missing
if not exist "%WIN32_WHLS%" mkdir "%WIN32_WHLS%"
if not exist "%ARM64_WHLS%" mkdir "%ARM64_WHLS%"
if not exist "%WIN32_SITEPKG%" mkdir "%WIN32_SITEPKG%"
if not exist "%ARM64_SITEPKG%" mkdir "%ARM64_SITEPKG%"

REM List of libraries to download
set "LIBS=flask flask-socketio pyserial pynput sounddevice numpy mss opencv-python Pillow scipy"

REM Download win32 wheels
echo.
echo ⬇️  Downloading win32 packages...
pip download --only-binary=:all: --platform win32 --python-version 3.11 --implementation cp --abi cp311 %LIBS% -d "%WIN32_WHLS%"

REM Download arm64 wheels
echo.
echo ⬇️  Downloading arm64 packages...
pip download --only-binary=:all: --platform win_arm64 --python-version 3.11 --implementation cp --abi cp311 %LIBS% -d "%ARM64_WHLS%"

REM Extract win32 wheels
echo.
echo 📦 Extracting win32 wheels...
for %%F in ("%WIN32_WHLS%\*.whl") do (
    echo     → %%~nxF
    tar -xf "%%F" -C "%WIN32_SITEPKG%"
)

REM Extract arm64 wheels
echo.
echo 📦 Extracting arm64 wheels...
for %%F in ("%ARM64_WHLS%\*.whl") do (
    echo     → %%~nxF
    tar -xf "%%F" -C "%ARM64_SITEPKG%"
)

echo.
echo ✅ All done! Packages extracted into embedded site-packages.
pause
exit /b