@echo off
set OMP_NUM_THREADS=1
set MKL_NUM_THREADS=1
set OPENBLAS_NUM_THREADS=1
set NUMEXPR_NUM_THREADS=1
cd /d E:\PaperSubmissions2026\Assembly_Skill_Learning\Expt_22a_Organic_Value_Learner
"C:\Users\hsmazumdar\AppData\Local\Programs\Python\Python313\python.exe" run_expt22a.py --workers 12 --full-reps 12 --abl-reps 4 --abl-boxes 15000 --max-boxes 20000 --skip-tests > results\main_stdout.log 2> results\main_stderr.log
