# KAIROS 042 — KR1
Research-only Python 3.10+ standard library. No operational actions. Model-relative finite-horizon Bellman decision planner with latent good/bad opportunity states, up to three fixed candidate models, binary cue and inspection, supplied priors and costs. Horizon 1–5, inspections 0–2. Commit/decline terminate; wait consumes time; inspect measures present at a fee before state transition; reserve once pays fee, locks gain and extends expiry one tick, leaving the option to decline. No rollback of commitment. GuardedPlanner removes commitment if any live candidate has negative conditional expected payoff, not a trajectory safety guarantee. Inputs require valid normalized belief and reachable state. Cache bounded in entries. No calibrated probability, automatic action, causal discovery or actual reservation.

Main/fresh seeds 42001–42008 / 42101–42108, 7 regimes, 7 policies, 784 exhaustive finite probability-tree evaluations. Followup 42201–42208, 7 regimes, 6 policies, 336 evaluations. 168 fixture/regime configurations (offer/prior seeds paired across regimes), 1120 evaluations. Matched action budgets are ceilings, not forced equal utilization. All fees paid; compute costs excluded. Exact means exhaustive probability-tree evaluation with floating-point arithmetic, not symbolic exactness. Full-information oracle upper bound, not attainable blind policy. Four Monte Carlo controls of 5000 trajectories, all within 1.65 estimated SE of exact estimates (one zero variance). Nine tests pass normal/optimized. Initial missing zero-utility counter key fixed; failed log retained.

Main/fresh average utility:
| Regime | Greedy | Myopic | Inspect-first | Wait-first | Reserve-first | Plan | Ensemble |
|---|---:|---:|---:|---:|---:|---:|---:|
|Matched|3.758|4.688|0.663|4.519|2.004|5.216|5.200|
|Stable|3.758|4.341|1.496|3.946|2.474|4.397|4.319|
|Fleeting|3.758|3.341|-2.505|3.232|-1.422|2.276|2.376|
|Emerging|3.758|6.272|3.625|6.365|4.754|8.414|8.436|
|False cue|-0.539|-2.215|-2.450|-2.330|-3.874|-3.833|-3.821|
|Weak test|3.758|4.548|-0.152|4.519|2.004|4.891|5.001|
|Abrupt|3.758|4.665|-1.452|5.290|0.388|4.292|4.652|

Aggregate plan/myopic/ensemble 3.665/3.663/3.738 utility. Oracle 10.218. Posthoc skeptical ensemble (nominal, inverted cue, abrupt) vs guarded identical ensemble across 56 fresh configurations: utility 3.590 vs 1.906, harmful commitment probability 19.84% vs 6.25%, commitment 70.58% vs 21.17%. False-cue plan -2.734, skeptical .634, guarded 1.366. No general dominance. Model alternatives supplied after initial observations.

Staged local SENSATION replay: 36 six-tick trajectories, 432 selective hash-verified scans, 180 policy replays. All scans match staged truth; observer unchanged contents/mtime. Synthetic cues, sentinel only consumed upon inspection; target only for scoring. Greedy/myopic/plan/skeptical/guarded mean utility 2.278/-.568/-.790/3.283/1.500; harmful commits 2/8/8/2/0 out of 36 each. No actual user devices or commitments.

Verified core blob b06d6a7a2df1f6ea597d5fb2266e330d649cc078. Complete KAIROS-042.zip SHA256 621cf2ffd5a6f6c6533114e8e5d2fd4b910fda80fecf92290235d354224a31f8 includes tests, benchmarks, results, inherited modules and logs. Tests/benchmarks not ported this pass. No remote CI, security audit or main merge. Existing formats unchanged.
