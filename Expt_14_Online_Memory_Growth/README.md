# Expt-14 — Online memory growth with chronological evaluation

Tests whether the frozen table lacked relevant experience. Three primary conditions on identical, predeclared task streams: primitive, frozen exact memory, growing exact memory. Each box is solved with only the memory available before it; the growing agent's completed solve is then inserted (first write wins) and insertion is billed to that box. Each independent stream gets its own memory copy starting from the same frozen base table. Retrieval is exact (mask, inventory) identity; transformation matching is excluded from the primary comparison. Independent fresh inventories and recurring-family workloads are kept separate.

```text
python -m pytest -q
python run_expt14.py --audit
python run_expt14.py --smoke
python run_expt14.py --diagnostic
```
