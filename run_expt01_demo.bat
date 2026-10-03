@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "EXPT=%~dp0Expt_01_10x10_Packing"
set "PY=%~dp0.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=%EXPT%\.venv\Scripts\python.exe"
if not exist "%PY%" (
    echo Python environment was not found.
    echo From this folder, create one with:
    echo   python -m venv .venv
    echo   .venv\Scripts\python -m pip install -r requirements.txt
    pause
    exit /b 1
)
if not exist "%EXPT%\run_gui.py" (
    echo Expt-1 GUI script was not found.
    pause
    exit /b 1
)
echo Starting the Expt-1 packing demo.
echo Close the packing window to stop.
echo This demo is not a saved experimental result.
start "MGA Expt-1 Demo" "%PY%" "%EXPT%\run_gui.py" --demo
exit /b 0
