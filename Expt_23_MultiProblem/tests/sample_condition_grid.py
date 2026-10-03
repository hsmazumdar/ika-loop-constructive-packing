import sys, time, pathlib
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
import generator as G, baselines as B
from env import Env
print("Condition grid on the same sample problems: capped/uncapped x natural/any-legal placing (100 episodes; beam w=64 natural only for capped)")
for sp,j in (("train",0),("test_iid",1),("test_size",1),("test_piece",0),("legacy",0)):
    for cap in (14,None):
        p=G.make_problem(sp,j,budget=cap)
        row=[]
        for nat in (True,False):
            u=B.evaluate_policy(p,B.run_uniform,100,9_000_000,natural=nat).mean()
            h=B.evaluate_policy(p,B.run_hand,100,9_000_000,natural=nat).mean()
            t=time.time(); b,_=B.run_beam(Env(p),width=64,natural=nat); tb=time.time()-t
            row.append("natural=%s uniform %6.2f hand %6.2f beam64 %3d (%.1fs)"%(nat,u,h,b,tb))
        print("%-18s cap=%-4s | %s | %s"%(p.pid,cap," | ".join(row[:1]),row[1]),flush=True)