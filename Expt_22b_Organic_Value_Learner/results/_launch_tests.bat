@echo off
cd /d E:\PaperSubmissions2026\Assembly_Skill_Learning\Expt_22b_Organic_Value_Learner
set OMP_NUM_THREADS=1
python -m pytest -q -x > results\pytest_out.txt 2>&1
