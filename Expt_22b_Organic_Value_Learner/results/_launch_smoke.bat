@echo off
cd /d E:\PaperSubmissions2026\Assembly_Skill_Learning\Expt_22b_Organic_Value_Learner
set OMP_NUM_THREADS=1
python run_expt22b.py --smoke --workers 1 > results\smoke_out.txt 2>&1
