import sys, time, pathlib, csv
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
import generator as G, baselines as B
from env import Env
out=pathlib.Path(__file__).resolve().parents[1]/"results"/"headroom_per_problem.csv"
rows=[]
for sp in ("train","test_iid","test_size","test_piece","test_both"):
    for j in range(30):
        p=G.make_problem(sp,j); e=Env(p)
        u=B.evaluate_policy(p,B.run_uniform,60,9_100_000).mean(); h=B.evaluate_policy(p,B.run_hand,60,9_100_000).mean()
        t=time.time(); b,_=B.run_beam(e,width=64); tb=time.time()-t
        rows.append([p.pid,sp,p.H,p.W,len(p.catalogue),len(p.blocked),e.free_cells,round(u,3),round(h,3),b,round(tb,2)])
with open(out,"w",newline="") as fh:
    w=csv.writer(fh); w.writerow("pid split H W k obstacles free uniform hand beam64 beam_s".split()); w.writerows(rows)
A=np.array([[r[7],r[8],max(r[9],r[8]),r[10]] for r in rows]); sp=np.array([r[1] for r in rows])
for s in ("train","test_iid","test_size","test_piece","test_both"):
    m=sp==s; a=A[m]
    print("%-10s n=%d uniform/ref %.3f hand/ref %.3f  frac(hand/ref<0.90)=%.2f  frac(<0.85)=%.2f  beam s mean %.2f"%(s,m.sum(),(a[:,0]/a[:,2]).mean(),(a[:,1]/a[:,2]).mean(),(a[:,1]/a[:,2]<0.9).mean(),(a[:,1]/a[:,2]<0.85).mean(),a[:,3].mean()))