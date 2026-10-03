@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Packing reviewer launcher
echo.
echo  Constructive packing with memory - reviewer repository
echo  Folder: %CD%
echo  This copy includes the experiments, saved runs, and supplementary materials.
echo  The manuscript (V2) is in the _Manuscript folder.
echo.

:menu
echo  ----------------------------------------
echo   1  Open reviewer guide
echo   2  Open supplementary tables (Part A)
echo   3  Open supplementary figures (Part A)
echo   4  Run unit tests
echo   5  Open Expt-1 demo window
echo   6  Open Expt-22e closure report (Part B)
echo   0  Exit
echo  ----------------------------------------
echo  Unit tests do not create a new scientific run.
echo  Smoke, diagnostic and stream commands are intentionally not on this menu.
echo  ----------------------------------------
set "CHOICE="
set /p CHOICE=  Choose [0-6]: 

if "%CHOICE%"=="1" goto do_guide
if "%CHOICE%"=="2" goto do_tables
if "%CHOICE%"=="3" goto do_figures
if "%CHOICE%"=="4" goto do_tests
if "%CHOICE%"=="5" goto do_demo
if "%CHOICE%"=="6" goto do_report22e
if "%CHOICE%"=="0" exit /b 0
echo  Invalid choice.
goto menu

:do_guide
start "" notepad "%~dp0REVIEWER_GUIDE.md"
goto menu

:do_tables
call "%~dp0open_tables.bat"
goto menu

:do_figures
call "%~dp0open_figures.bat"
goto menu

:do_tests
call "%~dp0run_unit_tests.bat"
goto menu

:do_demo
call "%~dp0run_expt01_demo.bat"
goto menu

:do_report22e
start "" notepad "%~dp0Expt_22e_Closure_Analyses\results\20261001_122457_run\report.md"
goto menu
