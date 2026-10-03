@echo off
set OMP_NUM_THREADS=1
set OPENBLAS_NUM_THREADS=1
set MKL_NUM_THREADS=1
cd /d E:\PaperSubmissions2026\Assembly_Skill_Learning\Expt_22d_Long_Ablations_Saturation
python run_expt22d.py --workers 26 --long-reps 6 --long-boxes 60000 --abl-reps 4 --abl-boxes 32000 --tag main > main_stdout.txt 2>&1
