@echo off
set OMP_NUM_THREADS=1
set OPENBLAS_NUM_THREADS=1
set MKL_NUM_THREADS=1
cd /d K:\PaperSubmissions2026\Assembly_Skill_Learning\Expt_22d_Long_Ablations_Saturation
echo %date% %time% resume start >> results\20261001_060654_main\progress.log
python run_expt22d.py --resume-dir results\20261001_060654_main --workers 13 --long-reps 6 --long-boxes 60000 --abl-reps 4 --abl-boxes 32000 > resume_stdout.txt 2>&1
python run_expt22d.py --report-only results\20261001_060654_main > resume_report_stdout.txt 2>&1
echo %date% %time% resume + report finished >> results\20261001_060654_main\progress.log
