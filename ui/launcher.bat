
@echo off
cd /d "%~dp0"

echo Launching Nana Warmzone Controller frontend...
start "" venv\Scripts\python.exe web.py

echo Launching backend processor...
start "" venv\Scripts\python.exe backend.py

exit