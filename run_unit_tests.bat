@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
set "ROOT=%~dp0"
set "PY=%ROOT%.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=%ROOT%Expt_02_Autonomous_Abstraction\.venv\Scripts\python.exe"
if not exist "%PY%" (
    echo Python environment was not found:
    echo   %ROOT%.venv\Scripts\python.exe
    echo Create it from this folder:
    echo   python -m venv .venv
    echo   .venv\Scripts\python -m pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
echo Unit tests only. No diagnostic and no smoke will be started.
echo A pass does not mean memory reduced deliberation or that the learner improved.
echo.

set "FAIL=0"

call :run "%ROOT%Expt_01_10x10_Packing"
call :run "%ROOT%Expt_02_Autonomous_Abstraction"
call :run "%ROOT%Expt_03_Mined_Operation_Library"
call :run "%ROOT%Expt_04_Emergent_Hierarchical_Abstraction"
call :run "%ROOT%Expt_04B_Selective_Reuse"
call :run "%ROOT%Expt_04C_Confirm_Reusable_Knowledge"
call :run "%ROOT%Expt_04D_Where_Reuse_Loses_Advantage"
call :run "%ROOT%Expt_04D2_Costly_Choices"
call :run "%ROOT%Expt_05_Consult_and_Commit_Gates"
call :run "%ROOT%Expt_06_Frozen_Library_Opportunity"
call :run "%ROOT%Expt_07_Indexed_Retrieval"
call :run "%ROOT%Expt_07B_Decision_Audit"
call :run "%ROOT%Expt_08_Action_Level_Value"
call :run "%ROOT%Expt_08B_Consistent_Labels"
call :run "%ROOT%Expt_08C_Unseen_Confirmation"
call :run "%ROOT%Expt_09_Exact_Continuation_Reuse"
call :run "%ROOT%Expt_10_Exact_Subproblem_Reuse"
call :run "%ROOT%Expt_11_Remaining_State_Equivalence"
call :run "%ROOT%Expt_12_Mixed_Stream_Recurrence"
call :run "%ROOT%Expt_13_Unforced_Reuse"
call :run "%ROOT%Expt_14_Online_Memory_Growth"
call :run "%ROOT%Expt_15_Local_Subproblem_Memory"
call :run "%ROOT%Expt_16_Search_Acquired_Local_Memory"
call :run "%ROOT%Expt_17_Arrangement_Census"
call :run "%ROOT%Expt_18_Arrangement_Utility"
call :run "%ROOT%Expt_19_Budgeted_Recognition"
echo.
echo Part B suites (Expt-20 to Expt-22d) and Part C (Expt-23) take several minutes.
set OMP_NUM_THREADS=1
set OPENBLAS_NUM_THREADS=1
set MKL_NUM_THREADS=1
call :run "%ROOT%Expt_20_Winning_Combination_LTM"
call :run "%ROOT%Expt_21_Continuous_Learning_Memory"
call :run "%ROOT%Expt_22a_Organic_Value_Learner"
call :run "%ROOT%Expt_22b_Organic_Value_Learner"
call :run "%ROOT%Expt_22c_Long_Streams"
call :run "%ROOT%Expt_22d_Long_Ablations_Saturation"
echo.
echo Part C suite (Expt-23).
call :run "%ROOT%Expt_23_MultiProblem"

echo.
if "%FAIL%"=="0" (
    echo All listed unit-test suites passed.
) else (
    echo One or more suites failed. Scroll up for the pytest output.
)
pause
exit /b %FAIL%

:run
if not exist "%~1\tests" (
    echo [skip] no tests directory: %~1
    exit /b 0
)
echo ----------------------------------------
echo %~1
echo ----------------------------------------
pushd "%~1"
"%PY%" -m pytest -q
if errorlevel 1 set "FAIL=1"
popd
exit /b 0
