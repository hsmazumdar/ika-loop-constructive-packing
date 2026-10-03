import os
os.environ["OMP_NUM_THREADS"]="1"; os.environ["OPENBLAS_NUM_THREADS"]="1"
import sys, time, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
import numpy as np
import variants as V, learner as Lr
from env import Env
from encode import Encoder
ag=Lr.Agent(0)
t0=time.time(); ns=0; ncand=[]
for j in range(60):
    p=V.make("std","train",j); t=time.time(); e=Env(p); enc=Encoder(e); tb=time.time()-t
    s,ep=ag.play(e,enc,np.random.default_rng(j),1.0,0.1,True)
    ag.online_step(ep); ns+=1
print("std: %.3f s/episode (play+online step, incl env build)"%((time.time()-t0)/ns))
t0=time.time()
for j in range(60):
    p=V.make("hard","train",j); e=Env(p); enc=Encoder(e); s,ep=ag.play(e,enc,np.random.default_rng(j),1.0,0.1,True); ag.online_step(ep)
print("hard: %.3f s/episode"%((time.time()-t0)/60))