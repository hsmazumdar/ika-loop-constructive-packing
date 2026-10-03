import os
for k in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS"): os.environ[k]="1"
import sys,time,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"src"))
import run_e_streams as R
R.CKPTS=(0,)
ev=R.evaluate
R.evaluate=lambda *a,**k: ev(*a,splits=("test_iid",),n_prob=6)
for arm in sys.argv[1:]:
    t=time.time(); r=R.run_stream(arm,"std","capped_nat",1,int(os.environ.get("NEP","1100")),print)
    print(arm,"%.0fs"%(time.time()-t),"meta events",r.get("n_meta_events"),"concepts",r.get("concepts"),"distinct/1000",r["distinct_per_1000"],flush=True)