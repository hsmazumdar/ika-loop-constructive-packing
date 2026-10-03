import os, sys
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'
sys.path.insert(0, r'E:\PaperSubmissions2026\Assembly_Skill_Learning\Expt_22a_Organic_Value_Learner')
os.chdir(r'E:\PaperSubmissions2026\Assembly_Skill_Learning\Expt_22a_Organic_Value_Learner')
# leaner eval for overnight finish
sys.argv = ['run_expt22a.py','--workers','10','--full-reps','12','--abl-reps','4','--abl-boxes','25000','--max-boxes','35000','--skip-tests']
# Patch Cfg defaults before import of run
import run_expt22a
# Monkeypatch main cfg_over by editing run module after... just exec main with patched defaults:
from pathlib import Path
import run_expt22a as R
# Reduce eval in the non-pilot branch by patching Cfg class default
from config import Cfg
Cfg.eval_boxes = 800
Cfg.probe_boxes = 60
sys.exit(R.main())
