@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "DOC=%~dp0supplementary\SUPPLEMENTARY_FIGURES.pdf"
if not exist "%DOC%" (
    echo Supplementary figures were not found:
    echo   %DOC%
    pause
    exit /b 1
)
echo Opening supplementary figures...
start "" "%DOC%"
exit /b 0
