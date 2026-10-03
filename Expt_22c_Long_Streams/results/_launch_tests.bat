@echo off
cd /d E:\PaperSubmissions2026\Assembly_Skill_Learning\Expt_22c_Long_Streams
set OMP_NUM_THREADS=1
python -m pytest -q > results\pytest_out.txt 2>&1
