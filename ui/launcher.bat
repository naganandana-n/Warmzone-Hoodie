@echo off
cd /d "%~dp0"
echo Launching Nana Warmzone Controller...
venv\Scripts\python.exe web.py
pause