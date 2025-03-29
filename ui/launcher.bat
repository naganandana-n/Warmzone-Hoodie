@echo off
cd /d "%~dp0"

echo Launching Nana Warmzone Controller frontend...
call venv\Scripts\python.exe web.py

echo Launching backend processor...
call venv\Scripts\python.exe backend.py

exit