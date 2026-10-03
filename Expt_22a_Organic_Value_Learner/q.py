import sys,time,pickle; sys.path.insert(0,'src')
import numpy as np
from stream import run_stream
from config import Cfg
v,seed,n=sys.argv[1],int(sys.argv[2]),int(sys.argv[3])
cfg=Cfg(); cfg.eval_boxes=300; cfg.checkpoints=(0,1000,2000,4000,6000,8000,10000,12000)
f=open(f"results/pilot_{v}_{seed}.log","w",buffering=1)
r=run_stream(v,seed,cfg,n,log=lambda m:f.write(m+"\n"))
f.write(str(r["runtime_s"])+" "+str({k:round(float(x["S1"].mean()),2) for k,x in r["evals"].items()})+"\n")
f.write("events %d\n"%len(r["events"]))
for e in r["events"]:
    if e["kind"]!="hyper" : f.write(str(e)+"\n")
