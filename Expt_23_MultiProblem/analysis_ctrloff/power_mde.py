import numpy as np, csv
from scipy import stats, optimize
def power(d,n,alpha):
    df=2*n-2; nc=d*np.sqrt(n/2); t=stats.t.ppf(1-alpha/2,df)
    return 1-stats.nct.cdf(t,df,nc)+stats.nct.cdf(-t,df,nc)
for alpha in (0.05,0.05/3):
    d=optimize.brentq(lambda x:power(x,8,alpha)-0.8,0.1,6); print("alpha %.4f  MDE d (80%% power, n=8 v 8, equal-variance t) = %.2f"%(alpha,d))
rows=[r for r in csv.DictReader(open("analysis_ctrloff/ctrloff_stream_scores.csv")) if r["folder"] in("results_ctrloff_i9","results_ctrloff_i7") and r["ckpt"]=="20000"]
for v in("std","hard"):
    sd={}
    for a in("F","N","NM","R","RN"):
        x=[float(r["score"]) for r in rows if r["variant"]==v and r["arm"]==a]; sd[a]=np.std(x,ddof=1)
    print(v,{k:round(s,4) for k,s in sd.items()})
    for a in("N","NM","R"):
        sp=np.sqrt((sd["F"]**2+sd[a]**2)/2); print("  F v",a,"pooled SD %.4f -> MDE diff at alpha .05: %.4f ; at .0167: %.4f"%(sp,sp*2.0*0+sp*optimize.brentq(lambda x:power(x,8,0.05)-0.8,0.1,6),sp*optimize.brentq(lambda x:power(x,8,0.05/3)-0.8,0.1,6)))
