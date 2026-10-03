import sys, time, pathlib
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
import generator as G, baselines as B
from env import Env
rows=[]
def run(prob, tag):
    e=Env(prob); N=100
    t=time.time(); u=B.evaluate_policy(prob,B.run_uniform,N,9_000_000).mean(); tu=(time.time()-t)/N
    t=time.time(); h=B.evaluate_policy(prob,B.run_hand,N,9_000_000).mean(); th=(time.time()-t)/N
    t=time.time(); b64,_=B.run_beam(e,width=64); tb=time.time()-t
    t=time.time(); b256,_=B.run_beam(e,width=256); tb2=time.time()-t
    ub=min(e.free_cells, (prob.budget or 10**6)*e.max_area)
    print("%-18s %-9s %2dx%-2d k=%2d obst=%2d cap=%s | UB %3d | uniform %6.2f hand %6.2f beam64 %3d beam256 %3d | t/ep uni %.3fs hand %.3fs beam64 %.1fs beam256 %.1fs"%(prob.pid,tag,prob.H,prob.W,len(prob.catalogue),len(prob.blocked),prob.budget,ub,u,h,b64,b256,tu,th,tb,tb2),flush=True)
for sp in ("train","test_iid","test_size","test_piece","test_both"):
    for j in range(2):
        run(G.make_problem(sp,j),"capped")
run(G.make_problem("legacy",0),"capped")
for sp,j in (("train",0),("test_size",0),("legacy",0)):
    run(G.make_problem(sp,j,budget=None),"uncapped")