@echo off
set OMP_NUM_THREADS=1
set OPENBLAS_NUM_THREADS=1
set MKL_NUM_THREADS=1
cd /d K:\PaperSubmissions2026\Assembly_Skill_Learning\Expt_22e_Closure_Analyses
python code\rerun_full_for_memory.py %1 results\20261001_122457_run\memory_reruns > results\20261001_122457_run\memory_reruns\stdout_s%1.txt 2>&1
