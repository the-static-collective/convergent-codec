# METAMORPHOSIS 037 — MT1

Research-only block-framed observation codec over IV1. Python 3.10+, standard library. Set PYTHONPATH=../invention-036:../accommodation-035:../curiosity-033:../perception-032:../interdependence-026 (POSIX). API encode(blocks,policy,cap=4) returns wire and selection receipts; decode(fields,wire) reconstructs observation deltas. Ordered baseline fields and labels shared externally. Each current buffered block can mine a fresh dictionary; admission based on actual compressed bytes. Only previously transmitted dictionaries are retained. LRU cache 1–8 dictionaries, default 4 for archive. Generic/grid fallbacks do not evict. Historical decode requires sequential replay, not independent random access. No autonomous causal discovery or cross-dictionary macro evolution. Greedy, not globally optimal. No security audit or hard RAM guarantee.

24 synthetic sequences, seeds 37001–37003 / 37101–37103, four regimes, 12 blocks x 16 states, 4608 maps. Clean baseline actually observed; subsequent maps synthetic. All six MT1 policies roundtrip exact (144 streams). Paid bytes include 7-byte header, six-byte block frames, mode, independent DEFLATE and 32-byte stream SHA-256. Whole-stream grid control pays compressed bytes + 32-byte digest allowance, no block boundaries. Shared fields excluded.

| Regime | Generic | Grid | Fixed | Reset | Hot | Archive | Whole grid |
|---|---:|---:|---:|---:|---:|---:|---:|
| Return |7864|6497|5465|5040|4612|4557|3001|
| Stable |7933|6603|4447|5037|4447|4447|2412|
| Novel |8620|7721|7721|7721|7721|7721|4804|
| Churn |8020|6802|6313|5735|5735|5418|3797|

42 dormant recalls; peak serialized cache 30 B (not Python overhead). Final return phase reset/hot/archive 1195/1088/1033. Whole-grid wins every aggregate. Two actual staged filesystem sequences, seeds 37801–37802, 8 blocks x12 observations: 192 complete observations matched fixture truth, 12 exact MT1 streams. Aggregate generic/grid/fixed/reset/hot/archive/whole-grid 1532/1258/1077/1015/948/930/643 B. Two dormant recalls. Eight local unit methods passed normal and optimized Python. No actual user device observations. No network, deployment, deletion or main merge.

Verified source blob 8ac1901a0cf152e8f031911ccc48e66450f29664. Full runnable package with inherited dependencies, tests, benchmarks, receipts, logs and hashes: METAMORPHOSIS-037.zip SHA256 592b836a7d6cc5c5d1092b04129104273e91e486c6849536d17bf9f85f89aade. Tests/benchmarks not ported upstream this pass. Remote CI not verified. Existing formats unchanged.
