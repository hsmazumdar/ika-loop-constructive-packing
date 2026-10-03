# Supplementary tables

These are the full audited tables. The main text uses the condensed tables in the parent folder.
Historical Expt-9 and Expt-10 recorded savings are unchanged, including primitive rows whose recorded saving is zero while total effort includes lookup overhead.
The two Expt-8C nets remain here. The report-derived net of −19,893 is not reconstructed from every decision record.
Table 8C names the retention summaries separately.

**Table 1. Experimental design and scope of inference across memory-reuse mechanisms**

| Mechanism | Experiments | Source of memory | Workload | Constructed intervention | Learning / evaluation separation | Principal question |
| --- | --- | --- | --- | --- | --- | --- |
| Primitive packing and early stored memory | Expt-1, Expt-2, Expt-2A, Expt-3 | Empty, short-term, or long-term stores; Expt-2 discovers flat operations during search | Repeated 10×10 inventories; Expt-2 held-out inventories | None in Expt-1. Expt-2 search is autonomous within a typed action language | Expt-2 library is frozen before its held-out comparison (Expt-2A) | Does stored or discovered memory change occupied cells once deliberation is counted? |
| Learned flat and hierarchical operations | Expt-4 through Expt-8C | Mined operations, selective libraries, consult/commit gates, an index, and action-level predictors | Held-out packing boxes; Expt-8C uses 50 new boxes | None at deployment. Expt-6 and Expt-8C use diagnostic remaining-solves | Libraries and gates are frozen before the reported evaluation. Expt-8B’s eight-box holdout is development data, not Expt-8C | Can a learned operation be selected so that whole-box effort falls without losing quality? |
| Exact continuation recall | Expt-9, Expt-10 | One shared first-write table of exact remaining states | Stored inventories, fresh inventories, and, in Expt-10, labeled intermediate prefixes | Expt-10 intermediate prefixes are supplied and the covering is committed | The table is frozen before fresh evaluation. First write wins; seeds are not separate memories | Does exact recall replace search when the same state recurs? |
| Supplied and experience-selected transformations | Expt-11, Expt-12 | The same first-write table, plus a declared set of rotations and reflections | Constructed transformed remainders; Expt-12 mixes them into hidden streams at predeclared rates | Transformed suffixes and slot categories are supplied. The category is hidden at test in Expt-12 | Which transforms are kept is frozen before evaluation. Expt-12’s selected set is not the Expt-11 set | Can experience choose among supplied equivalences, and does that help when recurrence is partial? |
| Unforced recurrence and online growth | Expt-13, Expt-14 | Frozen exact table (Expt-13 also keeps the selected transforms). Expt-14 may insert its own solved states | Ordinary fresh and family streams, with no scheduled matches | None on the evaluation streams. A coverage pass is used only to select transforms before Expt-13 evaluation | Selection is frozen before Expt-13. Expt-14 grows one table per stream after each solve | Do ordinary trajectories meet a stored intermediate state, and does writing new states pay for itself? |
| Local-region acquisition and reuse | Expt-15, Expt-16 | Exact fillings of bounded free regions | Supplied regions in Expt-15 Test 1; ordinary trajectories in Test 2 and Expt-16 | Test 1 assigns regions and budgets. Expt-16 searches recorded late regions offline | Entries are frozen before evaluation. Expt-16 counterfactuals are diagnostic and below the recurrence threshold | Are late free regions a usable source of exact local solutions? |
| Recurring arrangements, diagnostic utility, and bounded recognition | Expt-17, Expt-18, Expt-19 | Connected groups of two or three pieces from acceptable primitive packings; translation removed by a declared rule | Fresh and family manifests. Expt-19’s decision set is validation fresh | None. Expt-18 replays sampled legal placements as a diagnostic oracle | The dictionary is frozen before fresh examination. Expt-19’s budget is set on development manifests before validation | Do small successful arrangements recur, are they useful if selected with hindsight, and can this recognizer expose them within the cost gate? |

Notes. 

**Table 2A. Expt-4C held-out quality and effort for selective libraries**

| Experiment | Condition | Sample structure | Mean Q | Mean A | Paired saving | Saving (%) | Quality-loss rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Expt-4C | Primitive baseline | 100 tasks × 10 seeds | 75.45 | 1,611.6 | 0.0 | 0.0% | 0.0% |
| Expt-4C | Selective flat library | 100 tasks × 10 seeds (10 libraries) | 75.42 | 1,923.1 | -311.6 | -19.3% | 11.0% |
| Expt-4C | Selective hierarchical library | 100 tasks × 10 seeds (10 libraries) | 75.14 | 2,250.7 | -639.1 | -39.7% | 14.5% |

Notes. 

**Table 2B. Expt-5 held-out quality and effort for consult and commit gates**

| Experiment | Condition | Sample structure | Mean Q | Mean A | Paired saving | Saving (%) | Quality-loss rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Expt-5 | Primitive baseline | 16 eval tasks × 3 seeds (3 libraries) | 75.60 | 1,442.2 | 0.0 | 0.0% | 0.0% |
| Expt-5 | Current selective library | 16 eval tasks × 3 seeds (3 libraries) | 75.40 | 2,157.8 | -715.5 | -49.6% | 4.2% |
| Expt-5 | Consult gate only | 16 eval tasks × 3 seeds (3 libraries) | 75.60 | 1,821.0 | -378.8 | -26.3% | 0.0% |
| Expt-5 | Commit gate only | 16 eval tasks × 3 seeds (3 libraries) | 75.44 | 2,170.4 | -728.1 | -50.5% | 4.2% |
| Expt-5 | Both gates | 16 eval tasks × 3 seeds (3 libraries) | 75.60 | 1,821.0 | -378.8 | -26.3% | 0.0% |

Notes. 

**Table 2C. Expt-7 held-out quality and effort for indexed retrieval**

| Experiment | Condition | Sample structure | Mean Q | Mean A | Paired saving | Saving (%) | Quality-loss rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Expt-7 | Primitive baseline | 48 paired eval boxes | 75.54 | 1,449.1 | 0.0 | 0.0% | 0.0% |
| Expt-7 | Frozen gates, no index | 48 paired eval boxes | 75.54 | 1,838.1 | -389.0 | -26.8% | 0.0% |
| Expt-7 | Indexed retrieval | 48 paired eval boxes | 75.27 | 1,656.1 | -207.0 | -14.3% | 10.4% |
| Expt-7 | Indexed ranker | 48 paired eval boxes | 75.54 | 1,471.3 | -22.2 | -1.5% | 0.0% |

Notes.  Each Expt-7 seed uses its own frozen library. Snapshot hashes for seeds 11, 22, and 33 differ, and the run copies match those snapshots.

**Table 3A. Expt-8C frozen predictors on unseen action-level cases**

| Predictor | Evaluated actions | MAE | Accepted actions | Accepted unique boxes | Contributing seeds | Mean remaining saving | Mean net after site checks | Quality-loss rate | Severe-loss rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| per_seed_mean | 541 | 1,152.6 | 231 | 40 | 33 | 203.8 | 201.5 | 10.8% | 26.8% |
| frozen (historical) | 541 | 1,357.5 | 0 | 0 | Not applicable | Not recorded | Not recorded | Not recorded | Not recorded |
| context_unweighted | 541 | 1,151.4 | 4 | 3 | 33 | -415.0 | -418.2 | 25.0% | 25.0% |
| action_unweighted | 541 | 1,188.5 | 8 | 7 | 33 | 24.5 | 21.2 | 0.0% | 12.5% |
| context_weighted (historical) | 541 | 2,688.3 | 0 | 0 | Not applicable | Not recorded | Not recorded | Not recorded | Not recorded |
| action_weighted (historical) | 541 | 2,848.9 | 0 | 0 | Not applicable | Not recorded | Not recorded | Not recorded | Not recorded |

Notes. 

**Table 3B. Expt-8C action-model cost ledger, including rejected candidates**

| Component | Value | What is counted |
| --- | --- | --- |
| Gross accepted remaining saving | 196.0 | Sum of remaining-solve savings on the 8 accepted actions |
| Accepted-action decision cost in the saved ledger | 209.0 | Site checks and feature checks on accepted actions, as stored in offline.json |
| Consultation cost on every scored state | 1,608.0 | Index and ranking, including states whose action was rejected |
| Feature checks in the cost ledger | 17,167 | All first-legal action_vector cell inspections, accepted and rejected |
| Saved offline net (accepted features only) | -1,621.0 | Ledger field. The report states this subtracts accepted features only |
| Decision-relevant net including rejected features | -19,893 | Report-derived: accepted saving minus accepted site checks, all feature checks, rejected site checks, and all consultation |

Notes. 

**Table 4A. Expt-9 exact continuation recall**

| Experiment and task | Condition | Paired evaluations | Unique tasks | Mean A | Comparator A | Effort saving | Mean Q | Quality-loss rate | Initial hits | Intermediate hits | Validation failures |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Recurring stored inventories | Exact memory | 36 | 12 | 16.8 | 885.8 | 868.9 | 76.75 | 0.0% | Not recorded | Not recorded | 0 |
| Store primitive solves | Primitive | 36 | 12 | 900.8 | 885.8 | 0.0 | 76.36 | 0.0% | Not recorded | Not recorded | 0 |
| Fresh inventories | Exact memory | 36 | 12 | 1,267.1 | 1,250.8 | -16.4 | 75.97 | 0.0% | Not recorded | Not recorded | 0 |
| Fresh inventories | Primitive | 36 | 12 | 1,250.8 | 1,250.8 | 0.0 | 75.97 | 0.0% | Not recorded | Not recorded | 0 |

Notes. 

**Table 4B. Expt-10 exact subproblem recall, including labeled intermediate prefixes**

| Experiment and task | Condition | Paired evaluations | Unique tasks | Mean A | Comparator A | Effort saving | Mean Q | Quality-loss rate | Initial hits | Intermediate hits | Validation failures |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Recurring stored inventories | Exact memory | 36 | 12 | 16.5 | 1,238.0 | 1,221.5 | 75.92 | 5.6% | 36 | Not recorded | 0 |
| Constructed nonempty prefixes | Memory on | 30 | 10 | 181.3 | 1,611.5 | 1,430.2 | 76.00 | 0.0% | 0 | Not recorded | 0 |
| Constructed nonempty prefixes | Memory off | 30 | 10 | 1,611.5 | 1,611.5 | 0.0 | 75.30 | 0.0% | 0 | Not recorded | 0 |
| Fresh inventories | Exact memory | 36 | 12 | 1,680.0 | 1,663.1 | -16.9 | 75.56 | 0.0% | 0 | Not recorded | 0 |
| Fresh inventories | Primitive | 36 | 12 | 1,663.1 | 1,663.1 | 0.0 | 75.56 | 0.0% | 0 | Not recorded | 0 |

Notes. 

**Table 4C. Expt-11 supplied transformations and experience-selected transforms**

| Experiment and task | Condition | Paired evaluations | Unique tasks | Mean A | Comparator A | Effort saving | Mean Q | Quality-loss rate | Initial hits | Intermediate hits | Validation failures |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Transformed test remainders | Exact match | 33 | 11 | 1,003.1 | 990.8 | -12.3 | 75.52 | 0.0% | 0 | Not recorded | 0 |
| Transformed test remainders | All supplied transforms | 33 | 11 | 184.3 | 990.8 | 806.5 | 76.00 | 0.0% | 0 | Not recorded | 0 |
| Transformed test remainders | Learned selection | 33 | 11 | 184.3 | 990.8 | 806.5 | 76.00 | 0.0% | 0 | Not recorded | 0 |
| Transformed test remainders | Primitive | 33 | 11 | 990.8 | 990.8 | 0.0 | 75.52 | 0.0% | 0 | Not recorded | 0 |
| Fresh inventories | Learned selection | 36 | 12 | 1,886.0 | 1,835.3 | -50.7 | 75.50 | 0.0% | 0 | Not recorded | 0 |
| Fresh inventories | Primitive | 36 | 12 | 1,835.3 | 1,835.3 | 0.0 | 75.50 | 0.0% | 0 | Not recorded | 0 |

Notes. 

**Table 5. Expt-12 net effort in constructed mixed streams**

| Predeclared recurrence | Realized constructed share | Observed reuse | Primitive mean A | Exact-memory saving | Supplied-transform saving | Learned-selection saving | Quality-loss rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.0 | 0.0% | 1.4% | 1,399.6 | -14.7 | -95.5 | -37.5 | 0.0% |
| 0.05 | 4.2% | 5.6% | 1,981.5 | -15.5 | -47.2 | 11.9 | 0.0% |
| 0.1 | 8.3% | 8.3% | 1,466.4 | 45.5 | -8.5 | 47.0 | 0.0% |
| 0.25 | 25.0% | 25.0% | 1,553.7 | 219.2 | 309.1 | 354.4 | 0.0% |
| 0.5 | 50.0% | 51.4% | 1,810.8 | 502.0 | 857.2 | 887.1 | 0.0% |
| 1.0 | 100.0% | 100.0% | 1,404.2 | 659.8 | 1,319.2 | 1,319.2 | 0.0% |

Notes. 

**Table 6A. Expt-13 unforced reuse on ordinary streams**

| Workload | Memory condition | Streams | Boxes per stream | Initial hits | Intermediate hits | Mean cumulative saving per stream | Range across streams | Saving on never-encountered inventories | Quality losses |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Independent fresh | Exact memory | 3 | 24 | 0 | 0 | -391.0 | -395.0 to -387.0 | -16.3 | 0 |
| Independent fresh | Learned transforms | 3 | 24 | 0 | 0 | -1,564.0 | -1,580.0 to -1,548.0 | -65.2 | 0 |
| Recurring families | Exact memory | 3 | 36 | 12 | 0 | 4,727.0 | 3,545.0 to 6,932.0 | -16.4 | 0 |
| Recurring families | Learned transforms | 3 | 36 | 12 | 0 | 3,464.7 | 2,069.0 to 5,525.0 | -55.8 | 0 |

Notes. 

**Table 6B. Expt-14 chronological exact-memory growth**

| Workload | Memory condition | Streams | Boxes per stream | Initial hits | Intermediate hits | Mean cumulative saving per stream | Range across streams | Saving on never-encountered inventories | Initial keys | Final keys | Quality losses |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Independent fresh | Frozen exact | 6 | 30 | 0 | 0 | -490.5 | -504.0 to -481.0 | -16.4 | 684 | 684 | 0 |
| Independent fresh | Growing exact | 6 | 30 | 0 | 0 | -1,358.5 | -1,397.0 to -1,312.0 | -45.3 | 684 | 1089 to 1141 | 0 |
| Recurring families | Frozen exact | 6 | 30 | 11 | 0 | 1,129.3 | -504.0 to 2,242.0 | -16.3 | 684 | 684 | 0 |
| Recurring families | Growing exact | 6 | 30 | 15 | 0 | 936.3 | 66.0 to 1,404.0 | -45.9 | 684 | 1077 to 1109 | 0 |

Notes. 

**Table 7A. Expt-15 supplied-region component versus decomposed search and versus whole-box search**

| Comparison | Paired boxes | Mean Q of local policy | Mean A of local policy | Paired saving | Quality-loss rate |
| --- | --- | --- | --- | --- | --- |
| Local decomposed versus primitive decomposed, matched regions | 72 | 75.65 | 1,207.2 | 534.0 | 0.0% |
| Local decomposed versus whole-box primitive, matched regions | 72 | 75.65 | 1,207.2 | 15.2 | 11.1% |

Notes. 

**Table 7B. Expt-16 acquisition of late-region fillings and read-only applicability**

| Quantity | Value | Counting rule |
| --- | --- | --- |
| Regions examined | 128 | Recorded late regions in acceptable store trajectories |
| Exact fillings | 5 | Offline search found a complete filling |
| Area-impossible | 52 | Region size is not a sum of remaining piece sizes |
| Exhaustively impossible | 71 | Impossible count minus area-impossible count |
| Budget timeouts | 0 | Search stopped at the predeclared budget |
| Detection cost | 20,684 | Flood-fill cell visits during acquisition |
| Search cost | 58,413 | Candidate placements examined offline |
| Validation cost | 13 | Checks of found fillings |
| Insertion cost | 10 | Writes into the local table |
| Geometry matches, fresh | 3 | Read-only lookup on 60 fresh boxes |
| Inventory-compatible matches, fresh | 1 | Geometry match with the multiset available |
| Geometry matches, family | 2 | Read-only lookup on 60 family boxes |
| Inventory-compatible matches, family | 1 | Geometry match with the multiset available |
| Mean detector cost, fresh | 497.8 | Not primitive effort |
| Mean primitive effort, fresh | 1,597.7 | Same boxes, primitive policy |
| Mean detector cost, family | 497.1 | Not primitive effort |
| Mean primitive effort, family | 1,138.2 | Same boxes, primitive policy |

Notes. 

**Table 7C. Expt-16 diagnostic counterfactuals at the two inventory-compatible matches**

| Workload | Task | Region size | Primitive remaining effort | Commit remaining effort | Saving | Quality change | Quality loss |
| --- | --- | --- | --- | --- | --- | --- | --- |
| independent_fresh | inv_09f4d3398327 | 8 | 192.0 | 98.0 | 94.0 | 0.00 | no |
| recurring_family | inv_3c58e971670e | 8 | 384.0 | 962.0 | -578.0 | -1.00 | no |

Notes. 

**Table 7D. Expt-15 ordinary streams, without supplied regions**

| Workload | Condition | Boxes | Mean Q | Mean A | Paired saving versus primitive | Quality-loss rate | Local hits |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Independent fresh | Primitive | 60 | 75.20 | 1,822.2 | 0.0 | 0.0% | 0 |
| Independent fresh | Exact whole-box memory | 60 | 75.20 | 1,839.4 | -17.1 | 0.0% | 0 |
| Independent fresh | Local-region memory | 60 | 75.20 | 2,316.6 | -494.3 | 0.0% | 0 |
| Recurring families | Primitive | 60 | 75.98 | 1,118.3 | 0.0 | 0.0% | 0 |
| Recurring families | Exact whole-box memory | 60 | 75.98 | 1,134.2 | -15.9 | 0.0% | 0 |
| Recurring families | Local-region memory | 60 | 75.98 | 1,623.3 | -505.0 | 0.0% | 0 |

Notes. 

**Table 8A. Expt-17 recurrence and legal-fit census**

| Quantity | Fresh | Family |
| --- | --- | --- |
| Boxes | 60 | 60 |
| Boxes with any legal fit | 59 | 60 |
| Boxes with an early or middle fit | 59 | 60 |
| Early fit events | 4,999 | 6,888 |
| Middle fit events | 2,089 | 2,206 |
| Late fit events | 19 | 36 |
| Mean primitive effort | 1,597.7 | 1,138.2 |
| Mean matching checks | 72,872.2 | 93,095.8 |
| Ratio of mean matching checks to mean primitive effort | 45.6 | 81.8 |

Notes. 

**Table 8B. Expt-18 diagnostic utility of a sampled set of legal placements**

| Quantity | Value |
| --- | --- |
| Sampled fresh boxes | 12 |
| Replayed fresh placements | 91 |
| Valid replays with quality loss beyond one cell | 25 |
| Valid replays | 91 |
| Boxes whose best quality-preserving saving meets the floor of 48 | 10 |
| Of those, empty-board early | 5 |
| Of those, middle | 5 |
| Diagnostic discovery checks | 5,764 |
| Diagnostic counterfactual effort, both branches | 342,742 |

Notes. 

**Table 8C. Expt-19 held-out recognition cost and sampled-reference recall**

| Quantity | Value |
| --- | --- |
| Fresh boxes | 60 |
| Mean recognition cost | 127.7 |
| Mean primitive effort | 1,125.0 |
| Ratio of means | 0.113 |
| Mean of per-box ratios | 0.138 |
| Predeclared cost gate | 0.10 of primitive effort |
| State recall | 0.623 |
| Mean of per-box retention ratios | 0.792 |
| Useful actions exposed | 69 |
| Budget exhausted before the state | 49 |
| Budget exhausted during the consultation | 24 |
| Anchor misses among useful reference actions | 0 |
| Unlabeled exposures | 198 |
| Ratio of summed retained saving to summed oracle saving | 0.744 |

Notes.  The mean of per-box retention ratios is the mean, over 39 boxes with a useful reference action, of retained saving divided by that box's oracle saving. The ratio of summed savings is 12345.0 / 16589.0. These summaries are different.

**Table S1. Run provenance, corrected results, and dataset reuse**

| Experiment | Authoritative directory | Config SHA-256 | Role |
| --- | --- | --- | --- |
| Expt-1 | Expt_01_10x10_Packing/results | Not recorded | environment smoke; read-only for later experiments |
| Expt-2 baseline | Expt_02_Autonomous_Abstraction/results/20260929_092518_discovery_smoke | 19944168bb0212e392fb31af8c8b15873cac2c556c5805a79b6c39f4ef6e2cdd | authoritative discovery smoke; later cap-progress runs are not this baseline |
| Expt-2A | Expt_02_Autonomous_Abstraction/results/20260929_110932_expt2a | dd22d9c981c70357a3534da2a9b09aec27a631d390a76b3f22bdef366c308219 | frozen-policy comparison |
| Expt-4C | Expt_04C_Confirm_Reusable_Knowledge/results/20260929_200422_confirm | f3d8eb2ae6bfa0f58e393575096a9e53aae9cecf5f8a72c6a64acf977b34db01 | authoritative confirm; smoke 20260929_200405 superseded |
| Expt-5 | Expt_05_Consult_and_Commit_Gates/results/20260929_212658_diagnostic | 89502b2fb268751f519b089e7c8e5cd6bad306012e6e486b62d39731750c36db | authoritative; smoke superseded |
| Expt-7 | Expt_07_Indexed_Retrieval/results/20260929_220030_diagnostic | 20c07c79fc706adf8b34fabf778071e419f62c84ad243224eb6c4fd5c5d7d577 | authoritative; 20260929_220009 lacks the frozen-gates cell |
| Expt-7B | Expt_07B_Decision_Audit/results/20260929_223742_diagnostic | e5c7fe56d7e97c24b4d857106ac77b64fb0baaf9087d6667a3644c6fb26b4978 | audit of the frozen ranker |
| Expt-8C | Expt_08C_Unseen_Confirmation/results/20260929_233422_diagnostic | 9a5d688da346b002920d2fea5f79b5e29e295b27b930a72902ba34a43d3e7ea3 | unseen action-level confirmation |
| Expt-9 | Expt_09_Exact_Continuation_Reuse/results/20260929_234344_diagnostic | 69daa5c3977167b2b050ba4fd7776c7463b94a5e4f394cf0227b0eafb841847e | authoritative diagnostic |
| Expt-10 | Expt_10_Exact_Subproblem_Reuse/results/20260930_055535_diagnostic | 1c48099dffe05894159b8e352e5a0473386eac94182a37f8cfa22d9b959a675f | authoritative diagnostic |
| Expt-11 | Expt_11_Remaining_State_Equivalence/results/20260930_060957_diagnostic | 45ffae7a1bfa3b0fccf19faf23ce707ca3fea4f581b246bcc658079a160afbd5 | authoritative diagnostic |
| Expt-12 | Expt_12_Mixed_Stream_Recurrence/results/20260930_061916_diagnostic | a5da6de24d10bd1193f50d99fc26afd1839823adfef65020f7816dd8fe9fee58 | authoritative diagnostic |
| Expt-13 | Expt_13_Unforced_Reuse/results/20260930_064034_diagnostic | 7efe29f8869c79397c5846462365bc4a5d1d34505279304aa89be07096237b3e | authoritative diagnostic |
| Expt-14 | Expt_14_Online_Memory_Growth/results/20260930_064836_diagnostic | a5de033c8d484c06b9ccce19870446a2bc1cc5376e2c0b1e0b1e1605d43e0501 | authoritative diagnostic |
| Expt-15 | Expt_15_Local_Subproblem_Memory/results/20260930_070329_diagnostic | 06fee83d54c3e57ee044edf53529d4359683a302b10a23b5ac5ce0f5fd9bb584 | authoritative; 20260930_065912 differs on fresh streams |
| Expt-16 | Expt_16_Search_Acquired_Local_Memory/results/20260930_071552_diagnostic | fa332f6d9783881d858296b4f073f7fecdd2adf11b29cc3a17b5267f0e7ba927 | corrected decision row; 20260930_071519 superseded only for that row |
| Expt-17 | Expt_17_Arrangement_Census/results/20260930_090000_diagnostic | b0c0587b4364400f20c21633d20316d26468a33e0f744fceee48db9c3f614415 | authoritative census |
| Expt-18 | Expt_18_Arrangement_Utility/results/20260930_091301_diagnostic | a9f727d5d03ea7c53e6a2556a40278584da4b0378d4884d2d0054926d300c0b1 | authoritative utility sample; smokes are pipeline checks |
| Expt-19 | Expt_19_Budgeted_Recognition/results/20260930_092450_diagnostic | 9461d8e80cc01f62dd7e0363f894a815531c713c1d05ed53ecad97cb4e298d1a | authoritative held-out recognition; smoke superseded |
| Expt-17 frozen dictionary | Expt_17_Arrangement_Census/results/20260930_090000_diagnostic/frozen.json | b02cd72c92b7a9f00b8660b7a54633a1cb93844c62d20ff98ae0812ea62c904c | Frozen arrangement dictionary reused by Expt-18 and Expt-19. This hash is the file hash, not a second experiment. |
| Shared manifests | Expt_16_Search_Acquired_Local_Memory/manifests |  | Expt-16 through Expt-19 reuse these frozen task lists. Validation fresh does not overlap applicability fresh. Eight validation-family ids also occur in applicability family and were excluded from the Expt-19 family score. |

Notes. 

**Table S2A. Expt-4C per-seed paired results**

| Condition | Seed | Boxes | Wins | Quality losses | Mean paired ΔA |
| --- | --- | --- | --- | --- | --- |
| selective_flat | 11 | 100 | 13 | 9 | -302.2 |
| selective_flat | 22 | 100 | 19 | 12 | -387.5 |
| selective_flat | 33 | 100 | 12 | 13 | -508.0 |
| selective_flat | 44 | 100 | 19 | 9 | -169.6 |
| selective_flat | 55 | 100 | 18 | 12 | -347.3 |
| selective_flat | 66 | 100 | 18 | 11 | -265.4 |
| selective_flat | 77 | 100 | 28 | 14 | -318.9 |
| selective_flat | 88 | 100 | 20 | 7 | -177.8 |
| selective_flat | 99 | 100 | 20 | 13 | -166.7 |
| selective_flat | 111 | 100 | 9 | 10 | -472.2 |
| selective_hierarchical | 11 | 100 | 12 | 6 | -306.0 |
| selective_hierarchical | 22 | 100 | 16 | 15 | -786.0 |
| selective_hierarchical | 33 | 100 | 15 | 16 | -658.5 |
| selective_hierarchical | 44 | 100 | 19 | 15 | -792.9 |
| selective_hierarchical | 55 | 100 | 14 | 15 | -857.2 |
| selective_hierarchical | 66 | 100 | 21 | 17 | -509.2 |
| selective_hierarchical | 77 | 100 | 22 | 20 | -977.0 |
| selective_hierarchical | 88 | 100 | 16 | 15 | -369.1 |
| selective_hierarchical | 99 | 100 | 6 | 12 | -751.4 |
| selective_hierarchical | 111 | 100 | 20 | 14 | -384.0 |

Notes. 

**Table S2B. Expt-5 per-seed paired evaluation**

| Experiment | Condition | Seed | Boxes | Mean Q | Mean A | Paired saving | Quality-loss rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Expt-5 | both_gates | 11 | 16 | 75.56 | 1,844.7 | -252.7 | 0.0% |
| Expt-5 | both_gates | 22 | 16 | 75.69 | 1,945.5 | -485.1 | 0.0% |
| Expt-5 | both_gates | 33 | 16 | 75.56 | 1,672.9 | -398.7 | 0.0% |
| Expt-5 | current_selective | 11 | 16 | 75.56 | 2,055.9 | -463.9 | 0.0% |
| Expt-5 | current_selective | 22 | 16 | 75.69 | 1,929.1 | -468.6 | 0.0% |
| Expt-5 | current_selective | 33 | 16 | 74.94 | 2,488.2 | -1,214.0 | 12.5% |
| Expt-5 | primitive | 11 | 16 | 75.56 | 1,592.0 | 0.0 | 0.0% |
| Expt-5 | primitive | 22 | 16 | 75.69 | 1,460.4 | 0.0 | 0.0% |
| Expt-5 | primitive | 33 | 16 | 75.56 | 1,274.2 | 0.0 | 0.0% |

Notes. 

**Table S2C. Expt-13 per-stream cumulative paired savings**

| Workload | Condition | Stream | Boxes | Cumulative saving | Intermediate hits |
| --- | --- | --- | --- | --- | --- |
| independent_fresh | exact | 0 | 24 | -391.0 | 0 |
| independent_fresh | exact | 1 | 24 | -395.0 | 0 |
| independent_fresh | exact | 2 | 24 | -387.0 | 0 |
| independent_fresh | learned | 0 | 24 | -1,564.0 | 0 |
| independent_fresh | learned | 1 | 24 | -1,580.0 | 0 |
| independent_fresh | learned | 2 | 24 | -1,548.0 | 0 |
| recurring_family | exact | 0 | 36 | 3,545.0 | 0 |
| recurring_family | exact | 1 | 36 | 6,932.0 | 0 |
| recurring_family | exact | 2 | 36 | 3,704.0 | 0 |
| recurring_family | learned | 0 | 36 | 2,800.0 | 0 |
| recurring_family | learned | 1 | 36 | 5,525.0 | 0 |
| recurring_family | learned | 2 | 36 | 2,069.0 | 0 |

Notes. 

**Table S2D. Expt-7 per-condition seed means**

| Split | Condition | Seed | Boxes | Mean Q | Mean A | Paired saving | Quality-loss rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  | both_gates_frozen | 11 | 16 | 75.06 | 2,161.9 | -309.1 | 0.0% |
|  | both_gates_frozen | 22 | 16 | 75.62 | 2,043.1 | -465.6 | 0.0% |
|  | both_gates_frozen | 33 | 16 | 75.94 | 1,309.2 | -392.2 | 0.0% |
|  | indexed_ranked | 11 | 16 | 75.06 | 1,876.9 | -24.1 | 0.0% |
|  | indexed_ranked | 22 | 16 | 75.62 | 1,596.7 | -19.2 | 0.0% |
|  | indexed_ranked | 33 | 16 | 75.94 | 940.3 | -23.3 | 0.0% |
|  | indexed_retrieval | 11 | 16 | 74.31 | 2,511.2 | -658.4 | 18.8% |
|  | indexed_retrieval | 22 | 16 | 75.88 | 1,053.1 | 524.4 | 0.0% |
|  | indexed_retrieval | 33 | 16 | 75.62 | 1,404.1 | -487.1 | 12.5% |
|  | primitive | 11 | 16 | 75.06 | 1,852.8 | 0.0 | 0.0% |
|  | primitive | 22 | 16 | 75.62 | 1,577.5 | 0.0 | 0.0% |
|  | primitive | 33 | 16 | 75.94 | 917.0 | 0.0 | 0.0% |

Notes. 

**Table S2E. Expt-9 per-seed paired evaluation**

| Split | Condition | Seed | Boxes | Mean Q | Mean A | Paired saving | Quality-loss rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| fresh | exact | 11 | 12 | 76.17 | 1,263.6 | -15.9 | 0.0% |
| fresh | exact | 22 | 12 | 75.75 | 1,084.1 | -16.5 | 0.0% |
| fresh | exact | 33 | 12 | 76.00 | 1,453.7 | -16.7 | 0.0% |
| fresh | primitive | 11 | 12 | 76.17 | 1,247.7 | 0.0 | 0.0% |
| fresh | primitive | 22 | 12 | 75.75 | 1,067.6 | 0.0 | 0.0% |
| fresh | primitive | 33 | 12 | 76.00 | 1,437.0 | 0.0 | 0.0% |
| recurring | exact | 11 | 12 | 76.75 | 16.8 | 884.8 | 0.0% |
| recurring | exact | 22 | 12 | 76.75 | 16.8 | 958.8 | 0.0% |
| recurring | exact | 33 | 12 | 76.75 | 16.8 | 763.2 | 0.0% |
| store | primitive | 11 | 12 | 76.75 | 917.5 | 0.0 | 0.0% |
| store | primitive | 22 | 12 | 76.50 | 990.4 | 0.0 | 0.0% |
| store | primitive | 33 | 12 | 75.83 | 794.6 | 0.0 | 0.0% |

Notes. 

**Table S2F. Expt-10 per-seed paired evaluation**

| Split | Condition | Seed | Boxes | Mean Q | Mean A | Paired saving | Quality-loss rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| constructed | memory_off | 11 | 10 | 75.40 | 1,580.7 | 0.0 | 0.0% |
| constructed | memory_off | 22 | 10 | 75.10 | 1,576.1 | 0.0 | 0.0% |
| constructed | memory_off | 33 | 10 | 75.40 | 1,677.6 | 0.0 | 0.0% |
| constructed | memory_on | 11 | 10 | 76.00 | 181.3 | 1,399.4 | 0.0% |
| constructed | memory_on | 22 | 10 | 76.00 | 181.3 | 1,394.8 | 0.0% |
| constructed | memory_on | 33 | 10 | 76.00 | 181.3 | 1,496.3 | 0.0% |
| fresh | exact | 11 | 12 | 75.75 | 1,637.6 | -16.5 | 0.0% |
| fresh | exact | 22 | 12 | 75.75 | 1,621.5 | -17.2 | 0.0% |
| fresh | exact | 33 | 12 | 75.17 | 1,780.9 | -17.0 | 0.0% |
| fresh | primitive | 11 | 12 | 75.75 | 1,621.1 | 0.0 | 0.0% |
| fresh | primitive | 22 | 12 | 75.75 | 1,604.2 | 0.0 | 0.0% |
| fresh | primitive | 33 | 12 | 75.17 | 1,763.9 | 0.0 | 0.0% |
| recurring | exact | 11 | 12 | 75.92 | 16.5 | 970.2 | 0.0% |
| recurring | exact | 22 | 12 | 75.92 | 16.5 | 1,038.8 | 8.3% |
| recurring | exact | 33 | 12 | 75.92 | 16.5 | 1,655.6 | 8.3% |
| store | primitive | 11 | 12 | 75.92 | 1,002.2 | 0.0 | 0.0% |
| store | primitive | 22 | 12 | 75.83 | 1,069.9 | 0.0 | 0.0% |
| store | primitive | 33 | 12 | 75.08 | 1,684.2 | 0.0 | 0.0% |

Notes. 

**Table S2G. Expt-14 per-stream cumulative paired savings**

| Workload | Condition | Stream | Seed | Boxes | Mean saving per box | Cumulative saving | Quality losses |
| --- | --- | --- | --- | --- | --- | --- | --- |
| independent_fresh | frozen_exact | 0 | 11 | 30 | -16.3 | -489.0 | 0 |
| independent_fresh | frozen_exact | 1 | 22 | 30 | -16.1 | -484.0 | 0 |
| independent_fresh | frozen_exact | 2 | 33 | 30 | -16.7 | -502.0 | 0 |
| independent_fresh | frozen_exact | 3 | 44 | 30 | -16.8 | -504.0 | 0 |
| independent_fresh | frozen_exact | 4 | 55 | 30 | -16.1 | -483.0 | 0 |
| independent_fresh | frozen_exact | 5 | 66 | 30 | -16.0 | -481.0 | 0 |
| independent_fresh | growing_exact | 0 | 11 | 30 | -45.6 | -1,367.0 | 0 |
| independent_fresh | growing_exact | 1 | 22 | 30 | -45.3 | -1,360.0 | 0 |
| independent_fresh | growing_exact | 2 | 33 | 30 | -43.7 | -1,312.0 | 0 |
| independent_fresh | growing_exact | 3 | 44 | 30 | -45.3 | -1,358.0 | 0 |
| independent_fresh | growing_exact | 4 | 55 | 30 | -46.6 | -1,397.0 | 0 |
| independent_fresh | growing_exact | 5 | 66 | 30 | -45.2 | -1,357.0 | 0 |
| independent_fresh | primitive | 0 | 11 | 30 | 0.0 | 0.0 | 0 |
| independent_fresh | primitive | 1 | 22 | 30 | 0.0 | 0.0 | 0 |
| independent_fresh | primitive | 2 | 33 | 30 | 0.0 | 0.0 | 0 |
| independent_fresh | primitive | 3 | 44 | 30 | 0.0 | 0.0 | 0 |
| independent_fresh | primitive | 4 | 55 | 30 | 0.0 | 0.0 | 0 |
| independent_fresh | primitive | 5 | 66 | 30 | 0.0 | 0.0 | 0 |
| recurring_family | frozen_exact | 0 | 11 | 30 | 44.6 | 1,337.0 | 0 |
| recurring_family | frozen_exact | 1 | 22 | 30 | 39.9 | 1,198.0 | 0 |
| recurring_family | frozen_exact | 2 | 33 | 30 | -16.8 | -504.0 | 0 |
| recurring_family | frozen_exact | 3 | 44 | 30 | 74.7 | 2,242.0 | 0 |
| recurring_family | frozen_exact | 4 | 55 | 30 | 68.4 | 2,053.0 | 0 |
| recurring_family | frozen_exact | 5 | 66 | 30 | 15.0 | 450.0 | 0 |
| recurring_family | growing_exact | 0 | 11 | 30 | 44.4 | 1,332.0 | 0 |
| recurring_family | growing_exact | 1 | 22 | 30 | 40.2 | 1,206.0 | 0 |
| recurring_family | growing_exact | 2 | 33 | 30 | 2.2 | 66.0 | 0 |
| recurring_family | growing_exact | 3 | 44 | 30 | 46.8 | 1,404.0 | 0 |
| recurring_family | growing_exact | 4 | 55 | 30 | 39.3 | 1,180.0 | 0 |
| recurring_family | growing_exact | 5 | 66 | 30 | 14.3 | 430.0 | 0 |
| recurring_family | primitive | 0 | 11 | 30 | 0.0 | 0.0 | 0 |
| recurring_family | primitive | 1 | 22 | 30 | 0.0 | 0.0 | 0 |
| recurring_family | primitive | 2 | 33 | 30 | 0.0 | 0.0 | 0 |
| recurring_family | primitive | 3 | 44 | 30 | 0.0 | 0.0 | 0 |
| recurring_family | primitive | 4 | 55 | 30 | 0.0 | 0.0 | 0 |
| recurring_family | primitive | 5 | 66 | 30 | 0.0 | 0.0 | 0 |

Notes. 

**Table S2H. Expt-18 family box-level diagnostic opportunities**

| Box index | Task | Ideal stage | Ideal saving | Meets floor |
| --- | --- | --- | --- | --- |
| 0 | inv_a8956340ad37 | Not applicable | 0.0 | no |
| 10 | inv_41ec58701360 | early | 636.0 | yes |
| 20 | inv_4dbbbf516584 | early | 132.0 | yes |
| 30 | inv_a21f4dc3bf54 | early | 36.0 | no |
| 40 | inv_5ba647788a08 | middle | 132.0 | yes |
| 50 | inv_6cf68140c244 | early | 84.0 | yes |

Notes. 

**Table S3. Cost definitions by experiment**

| Experiment | Deployment effort | Acquisition or learning cost | Diagnostic replay | Other recorded cost |
| --- | --- | --- | --- | --- |
| Expt-4C | A on final-test boxes | Not in the held-out A | Not applicable | Internal execution is a separate column and is not added here |
| Expt-5 | Primitive evaluations + retrieval + applicability + learned site checks + gate checks | Counterfactual gate labels, excluded from eval A | Not applicable | Not recorded as a second ledger in this table |
| Expt-7 / 7B | A, with consultation itemized | Ranker trained under the 1,600-cap labels | Recall rollouts are diagnostic | Budget 0 reproduces primitive A |
| Expt-8C | Not tested as a whole-box policy | Model fit is offline | Skip and commit remaining-solves | Feature checks: total in the ledger; rejected split is report-derived |
| Expt-9–14 | A = primitive evaluations + lookup + validation + learning, as each file’s A_identity records | Table construction is prior to fresh A except Expt-14 insertion, which is inside growing A | Not applicable | Storage bytes are in offline summaries where saved |
| Expt-15–16 | Agent A on evaluation boxes | Region search, detection, validation, insertion | Expt-16 counterfactuals | Detector cell visits are not primitive evaluations |
| Expt-17 | Not a deployed memory policy | Group checks during extraction, not placement evaluations | Not applicable | Matching checks are a separate census ledger |
| Expt-18 | Not tested | Not re-extracted | Both branches of every sampled placement | Discovery checks are separate from counterfactual A |
| Expt-19 | Not tested; commitment disabled | Dictionary is the frozen Expt-17 artifact | Reference counterfactuals, excluded from recognition cost | Recognition bills inventory, anchors, geometry, cache, and lookup |

Notes. 

**Table S4. Diagnostic controls, audits, and interpretation limits**

| Control or limit | What was checked | Result | Source class |
| --- | --- | --- | --- |
| Expt-4C lesion | Removing the library | Matched the primitive trace | computed in the confirm run; see Table 2A note |
| Expt-4C transfer | A library used across seeds | Matched the hierarchical condition on the saved means | report-derived from the confirm report’s identical published means |
| Expt-7B commitments | Whether the frozen ranker placed a library action | 0 committed decisions in 767 decision rows across 48 seed-task pairs | computed |
| Expt-7 operation versus action recall | Whether a shortlisted operation is the same thing as a placement | Operation recall is not placement recall | design |
| Expt-8 label budget | Whether pair_eval_cap was the remaining-solve budget | Expt-8 already used eval_cap minus prefix effort. Expt-7 labels used the 1,600 cap. Expt-8B replay changed 0 fit rows and 0 validation rows | report-derived from EXPERIMENT_HISTORY.md |
| Expt-8B holdout | Whether eight boxes were unseen confirmation | They are development boxes. Expt-8C is the unseen set | design |
| Expt-9–14 first write | Whether seeds keep separate best solutions | One shared table; first write wins; overwrites are counted and not stored | design |
| Expt-11 sample size | What 33 rows are | 11 tasks from four families × 3 seeds | design |
| Expt-16 fillings | Whether the primitive found the five fillings | It missed those five. It did not miss none. Most regions were impossible | computed |
| Expt-18 oracle | Whether box savings add candidate suffixes | No. The box figure is one selected candidate | computed |
| Expt-19 anchors | Anchor misses inside the sampled reference | None in that sample. Coverage of all useful placements was not measured | computed |
| Expt-19 gate | Whether recall can waive the cost gate | No. The recognizer failed 0.10. Commitment was not tested | computed |

Notes. 
