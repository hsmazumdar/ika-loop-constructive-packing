# Expt-13 — Unforced reuse during ordinary search

Frozen Expt-11/12 mechanism (exact lookup, declared D4 candidates, Expt-11 selection rule). The shared continuation table and the selected transformation set are frozen before evaluation. Evaluation uses no constructed prefixes, no scheduled matching states, and no task-category input. Every agent chooses its own actions.

Two labelled workloads:

- Independent fresh inventories: incidental reuse under the original distribution.
- Recurring task families with varying inventories: a family is a type-set declared before evaluation; variants are independent packings restricted to that type-set. The generator does not consult the memory table.

Agents: primitive, exact memory, learned-transform memory, on identical starts and paired seeds. Results are summarised across independent streams; seeds are paired comparisons, not independent learned memories. Online memory growth is not part of this experiment.

```text
python -m pytest -q
python run_expt13.py --audit
python run_expt13.py --smoke
python run_expt13.py --diagnostic
```
