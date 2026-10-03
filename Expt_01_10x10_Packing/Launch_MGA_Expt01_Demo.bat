@echo off
title MGA Expt-1 Demo Launcher
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Local virtual environment not found.
    echo Create it with:
    echo     python -m venv .venv
    echo     .venv\Scripts\python -m pip install -r requirements.txt
    pause
    exit /b 1
)

echo Starting Memory-Guided Assembly  /  Expt-1 demo...
echo The packing window should open in training mode (STM + LTM).
echo Close the window to stop.
echo.

start "MGA Expt-1 Demo" "%~dp0.venv\Scripts\python.exe" "%~dp0run_gui.py" --demo
