# HOMEOSTASIS 029 — repair budget regulation

Research-only simulator. Run from this directory with PYTHONPATH=../interdependence-026. Python 3.10+, standard library. homeostasis.fixture(seed,regime), homeostasis.simulate(fixture,policy,lifetime=100000). The controller uses only observed inventory losses, online peers, elapsed time, known horizon and expenditure. EWMA risk signals and four-tick hysteresis are fixed heuristics, not learned calibrated probabilities. Paced reactive admits 25% of budget upfront, then 75% over the horizon. Emergency reserve requires newly observed inventory loss, and excess expenditure is restricted to urgent repairs. No live writes or deletion.

704 simulations, 33,792 ticks, 65,952 verified repairs including 1,018 parity-derived. Main: 512 runs, 8 seeds 2901–2908, four regimes, eight policies, 100k and 160k lifetime ceilings. Fresh follow-up: 192 runs, six seeds 2911–2916, reverse and late-shock regime transitions, frozen controller. Follow-up environments chosen posthoc. 48 ticks and 6500 B/tick. Matched event traces. Cost model inherited from ADAPTATION: encoded payload + 32 B address, regeneration input and output, excludes inventories, ingress, initial placement, parity metadata and filesystem overhead. Fixed existing parity.

Permanent losses (main 100k / fresh 100k / main 160k / fresh 160k):
- Reactive: 299 / 49 / 172 / 20
- Durable: 294 / 47 / 236 / 47
- Adaptive: 296 / 45 / 203 / 38
- Paced reactive: 259 / 58 / 170 / 28
- Switching only: 303 / 45 / 180 / 23
- Paced + reserve: 267 / 54 / 168 / 32
- Full controller: 264 / 59 / 180 / 31

Main shifted regime, 100k: reactive 58 permanent losses, paced 43, full 45. Fresh reverse: reactive 37, paced 54, switching 32, full 55. Fresh late shock: reactive 12, paced 4, durable 0, full 4. Pacing helps late losses but can hurt early failures. Full controller does not consistently beat simpler policies. Do not enable by default. Neither model risk nor actual probabilities are calibrated.

Six local tests passed normal and optimized Python, including baseline equivalence, causal prefix invariance, caps, hysteresis and reserve gating. 24 filesystem replays, 12 complete restores and 6 regenerated objects; all missing sets and recovered bytes verified. No production deployment, network, security audit, remote CI or main merge. Tests and benchmarks remain in separate package.

Verified upstream blobs: controller.py cdd305d576858f958491f6a2b6dbb9f849af74f1; homeostasis.py ad97ce7c7ba1ba5ae7f6005a520585196b849250. Complete source, tests, logs, results, SHA256SUMS in HOMEOSTASIS-029.zip, SHA256 078b39a48963a3ea8cc0e8e070c8f8ae94334697a27d98eef5b5393d3a581441. Existing formats unchanged.
