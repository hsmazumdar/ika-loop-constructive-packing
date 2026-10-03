import os
for k in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS"): os.environ[k]="1"
import sys,time,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"src"))
import run_streams as R
R.evaluate=lambda *a,**k:{}
R.CKPTS=()
arm,var,n=sys.argv[1],sys.argv[2],int(sys.argv[3])
t=time.time(); r=R.run_stream(arm,var,"capped_nat",1,n); print(arm,var,n,"eps: %.3f s/ep"%((time.time()-t)/n))