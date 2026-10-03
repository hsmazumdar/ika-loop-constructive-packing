@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "DOC=%~dp0supplementary\SUPPLEMENTARY_TABLES.docx"
if not exist "%DOC%" (
    echo Supplementary tables were not found:
    echo   %DOC%
    pause
    exit /b 1
)
echo Opening supplementary tables...
start "" "%DOC%"
exit /b 0
