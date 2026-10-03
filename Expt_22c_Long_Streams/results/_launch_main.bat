@echo off
cd /d E:\PaperSubmissions2026\Assembly_Skill_Learning\Expt_22c_Long_Streams
set OMP_NUM_THREADS=1
set OPENBLAS_NUM_THREADS=1
set MKL_NUM_THREADS=1
python run_expt22c.py --skip-tests --workers 12 --reps 12 --abl-reps 0 --boxes 32000 --abl-boxes 32000 --eval-boxes 1200 --variants "" --tag run --seed-offset 100 > results\main_stdout.log 2> results\main_stderr.log
