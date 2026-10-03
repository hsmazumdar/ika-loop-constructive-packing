@echo off
cd /d E:\PaperSubmissions2026\Assembly_Skill_Learning\Expt_22b_Organic_Value_Learner
set OMP_NUM_THREADS=1
set OPENBLAS_NUM_THREADS=1
set MKL_NUM_THREADS=1
python run_expt22b.py --skip-tests --workers 10 --reps 12 --abl-reps 4 --boxes 20000 --abl-boxes 10000 --eval-boxes 1200 > results\main_stdout.log 2> results\main_stderr.log
