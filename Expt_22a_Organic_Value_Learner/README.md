# Expt-22a — Organic Afterstate Value Learner

Value-based successor to Expt-21’s additive hash tables, under the **same handicap protocol**:
budget ≤14 pieces/box, natural placing (must touch wall/piece), held-out eval, weak baseline ~67 so learning gains are visible.

## Idea

1. **Afterstate features** (`feat.py`, D=29): geometry after a candidate placement + concept-library column.
2. **Value MLP** (`net.py`): 2×ReLU numpy network; fast net trained online; **slow** EMA net = LTM for eval/bootstrap; function-preserving `widen`.
3. **Placement**: 1-step lookahead — softmax(V(afterstate)/τ) over natural candidates (+ε). No hand packing rule in the policy.
4. **Learning**: λ-returns vs slow net; STM → **sleep** (prioritised replay + dream prefixes); concept library of promoted local arrangements.
5. **Meta-controller** (`meta.py`): adapts τ, ε, lr, λ, dream ratio, sleep interval, STM size from probe EMA gain + sleep-loss diagnostics.
6. **Growth**: shadow-widen capacity test only when stagnation suggests a bottleneck.

## Run

```bat
cd Expt_22a_Organic_Value_Learner
python -m pytest -q
python run_expt22a.py --pilot
python run_expt22a.py --workers 14
python run_expt22a.py --report-only results\<timestamp>_run
```

## Ablations (main protocol)

| variant | meaning |
|---|---|
| full | value + lookahead + sleep + dream + meta + concepts + shadow growth |
| no_meta | fixed V21-style anneal, no growth |
| no_sleep | online updates only |
| no_dream | sleep/replay without dreams |
| no_concepts | no concept library |
| mc_only | λ fixed to 1 (pure MC returns) |
| frozen | no weight updates |

## Comparison targets

- Frozen / uniform natural ≈ **67** S1 (V21: 67.30 held-out)
- V21 full held-out ≈ **83.70**
- Hand contact/hole rule (ref) ≈ **89.61**
- Stretch target **93**
