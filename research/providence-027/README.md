# PROVIDENCE 027 — scenario-weighted preservation

Research-only Python 3.10+ planner, using existing ID1 and CC1 modules. From this directory, set PYTHONPATH to ../interdependence-026 (on POSIX: PYTHONPATH=../interdependence-026 python -c 'import providence'). Python API: candidates(obj,base,seed), plan(obj,base,pool,budget,scenarios,rank_bonus=.25). Inputs are a hash-to-bytes mapping, six singleton-owner inventories, frozen candidate pool, encoded-byte ceiling, weighted peer-loss scenarios. Outputs: proposed inventories, parity records, parity bytes, charged cost and probe counts. No automatic writes or deletions. Current planner assumes nonempty singleton-owner fixture inventories and distinct equation payloads; not a hardened generic interface.

Every potential copy or parity equation is scored by incremental uniquely solvable variable count plus weighted rank gain, divided by encoded payload and record metadata cost. Greedy selection, not global optimum. Candidate pool includes all replica destinations and bounded size-neighbor/random groups. Rank bonus .25, ablation zero. Model uses whole padded variables.

Local experiments: 16 initial synthetic trials (seeds 2701–2704, equal and variable objects, 25% and 55% extra protection ceilings); eight fresh posthoc follow-up trials (2711–2714, 55%). 24 singleton objects across six peers. Targeted objective covers all singles and three paired failures; broad objective all singles and doubles; broad-triple includes triples. Weights chosen experimentally, not measured failure probabilities. Costs exclude transport, filesystem overhead and common metadata. Equal ceilings, unequal spend.

Fresh variable-size missing-object instances across 24 singles, 60 doubles, 80 triples:
- Replication: 20 / 176 / 504
- GF(256) two-parity stripes: 0 / 320 / 960
- Targeted: 8 / 169 / 570
- Broad: 11 / 122 / 573
- Broad-triple: 17 / 133 / 416

No complete triple restoration in these fresh trials. Broad reduces double missing instances 30.7% vs replication, broad-triple reduces triple missing 17.5%, but single-failure performance loses to GF(256). Equal-size broad: 9 / 162 / 937 versus stripes 0 / 192 / 960. Broad objectives are in-sample scenarios, not prediction of unseen failure shapes. No universal winner.

Real fixture: 273305 bytes, 26 objects, 69714 byte protection ceiling. 63 filesystem attempts (21 outages × 3 plans). Every missing set matched the algebraic model and every complete directory matched source manifest. Replication spent 66518, completed 1/21; stripes spent 66307, completed 4/21; targeted spent 65930, completed 2/21. All double outages incomplete. Targeted loses to existing controls here.

Three test methods pass in normal and optimized Python, including 500 random incremental-vs-full elimination checks per run, actual solver/model comparisons, cost bounds. Planner scans hundreds of candidates; no measured network costs, no security audit, no production activation. Downloadable PROVIDENCE-027.zip contains all benchmarks, inherited sources, tests and results. SHA256 7d80f227ebbd3408a0baacd00c763a04d53a84c20e10cc8de1ef4c791f3f2c41. Local planner blob e6fb282d9617feff3b28380cbecf5a2894761251. Tests and benchmarks not committed in this pass. Existing formats unchanged; remote CI unverified.
