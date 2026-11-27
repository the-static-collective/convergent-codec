# CONTEXT 040 — CT1
Research-only standard-library Python 3.10+. Set PYTHONPATH=../analogy-039. API Context(n,policy='active',capacity=4), enter(label), probe(pool), observe(x,y), predict(x). Inherits AN1 ternary vectors, bijections and global state flip. Bounded recent pairs (16, or 4 for window), cache of exactly identified maps (4 default), contextual label changes reset evidence, contradictions restart from newest pair. Cached predictions explicitly provisional; one matching distinct example, two for cautious. Active query combines cached output entropy and AN1 signature splitting. No calibrated probabilities, causal proof, automatic actions, persistence or deployment. Default API policy experimental.

Main/fresh seeds 40001–40004 / 40101–40104: 336 runs, six regimes, seven policies. Followup 40201–40206: 252 runs, seven regimes, six policies. Adds active-reset and near-map counterexample posthoc without tuning original policies. Each run eight bootstrap pairs, 40 follow-up pairs, 240 held-out queries, ten eight-tick epochs, alternate-tick probing. Same input pool, labels and test questions, no test answers fed back. 588 runs, 141120 queries, 23520 follow-up pairs plus 4704 bootstrap. Equal probe counts, not compute.

Follow-up correct/wrong/abstain, 1440 per regime/policy:
| Regime | Active reset | Active recall | Cautious recall |
|---|---|---|---|
| Labeled |457/0/983|1093/0/347|841/0/599|
| Hidden |410/162/868|1079/162/199|827/162/451|
| Alias |457/0/983|1093/0/347|841/0/599|
| Novel |472/0/968|472/0/968|472/0/968|
| Midshift |72/18/1350|396/72/972|180/72/1188|
| Outside |394/0/1046|847/0/593|667/0/773|
| Near |460/0/980|1116/22/302|858/10/572|

Near passive recall 638/53/749, label recall 688/0/752 (labels reliable here). Near active 22 provisional errors; hidden active 162 stationary-consensus errors; midshift active 54 provisional and 18 consensus errors. No safety guarantee from unique maps or cached compatibility. Staged local replay 40401–40402: 512 SN1 reports matched staged states, labeled 61/0/19, hidden 61/9/10. Eight tests passed normal and optimized Python. Includes explicit false-recall counterexample and causal prefix invariance. No actual operational user devices observed.

Source blob 3cc32a67ab8e251a3d2f06ffe2e9fa25232ef181 verified. Complete package CONTEXT-040.zip SHA256 f32b36b8e24d56d90fd0bd163c979fdb3ec914cac15fb41d368c2a3984a59b76. Tests, benchmarks, results, inherited modules in package, not ported this pass. No remote CI verification or merge. Existing formats unchanged.
