# ANTICIPATION 041 — AT1
Research-only Python 3.10+ standard-library wrapper around CT1/AN1. From this directory set PYTHONPATH=../context-040:../analogy-039 (POSIX). Anticipation(n,policy='periodic',width=10,budget=3,rates=None,seed=0). Boot once with pairs and label; step(label,cue) each tick; if True, probe(pool) and observe(x,y) before predicting. predict(x,max_age=None) yields prediction and basis, or abstains if latest probe in current label exceeds age limit. Probe age is not proof of validity. No automatic actions or actual clock. Rates is smoothed conditional disagreement among comparable probes, not calibrated change hazard. Unseen bins default .5; learned threshold .18 heuristic. All policies use same active CT1 query chooser. Equal budgets per ten ticks, not compute/read bytes. Periodic default.

28 training runs 41001–41004, 1008 probes, 663 comparable. Main/fresh 41101–41106 / 41201–41206: 840 runs, seven regimes, five policies. Third cohort 41301–41306: 756 runs, nine regimes, seven policies. 138 fixture/regime combinations, 1596 evaluation runs, 574560 prediction opportunities, 76608 probes, 12768 bootstrap pairs. Warning variants paired by seed, only cue timing differs. Gates evaluated on same predictions.

Original aggregate correct/wrong/abstain per policy/budget (30240):
| Budget | Periodic | Random | Burst | Adaptive | Learned |
|---|---|---|---|---|---|
| 30% |18633/1621/9986|18642/2694/8904|18222/2928/9090|18525/1760/9955|18841/1540/9859|
| 50% |23558/808/5874|23284/1414/5542|22895/2175/5170|23312/1025/5903|23648/1290/5302|

Third cohort aggregate (19440): periodic 11580/1219/6641 and 15198/718/3524 at 30/50%; learned 11663/1186/6591 and 15095/1021/3324; phase 11735/1285/6420 and 15031/694/3715; paced 11699/1272/6469 and 14991/811/3638. At 50%, matched-phase vs paced errors simultaneous warning 96 vs 27, early 96 vs 216, lagged 96 vs 99. No robust adaptive dominance, no change prediction without cues.

Original periodic 30% gate no limit 18633/1621/9986, age 2 17047/1243/11950, age 1 11751/512/17977, age 0 6107/75/24058. All 75 same-tick errors in near-map regime. Staged local replay 41401 warning / 41402 near: six runs, 1176 real SN1 scans all matched truth, 180 probes, 360 questions; periodic 75/11/34, phase 76/7/37, paced 75/8/37; age-zero errors 4/1/3. Eight tests passed normal and optimized Python; causal prefix, budget, same-tick counterexample. Actual user devices not observed.

Verified blobs: core b5e05574caec767318c3dcae4c77d0aca214de21, benchmark 2656718b98ae289bc4b4bfbec3f218e19bc788d6, tests eac796456579b3a5c48b8abd31103d5a416c4103. Complete ANTICIPATION-041.zip SHA256 4a46f98f43feb0321414f67d113f48127c953746f3af5d622e766b6e99b6d64f includes full dependencies, followup and replay scripts, raw results and logs. No remote CI verified, operational calibration, networking, repair, deployment or merge. Existing formats unchanged.
