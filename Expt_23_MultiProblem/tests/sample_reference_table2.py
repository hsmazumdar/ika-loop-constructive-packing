import sys, time, pathlib
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
import generator as G, baselines as B
from env import Env
print("pid | uniform | hand | beam64 | rollout-beam(w8,pp6,nr2) S1 (s) -- 100 eval episodes for uniform/hand")
for sp,j in (("train",0),("train",1),("test_iid",1),("test_size",0),("test_size",1),("test_piece",0),("test_both",1),("legacy",0)):
    p=G.make_problem(sp,j); e=Env(p)
    u=B.evaluate_policy(p,B.run_uniform,100,9_000_000).mean(); h=B.evaluate_policy(p,B.run_hand,100,9_000_000).mean()
    t=time.time(); b,_=B.run_beam(e,width=64); tb=time.time()-t
    t=time.time(); rb,_=B.run_beam_rollout(e,8,6,2); trb=time.time()-t
    print("%-18s %2dx%-2d k=%2d | %6.2f | %6.2f | %3d (%.1fs) | %3d (%.1fs)"%(p.pid,p.H,p.W,len(p.catalogue),u,h,b,tb,rb,trb),flush=True)