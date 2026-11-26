# JUBILEE 047 — JB1
Research-only Python 3.10+, release.py requires cryptography>=40 and CV1. Set PYTHONPATH=../reciprocity-046:../covenant-044:../telos-043 (POSIX). Memory separates lifetime directional gift totals from temporary allocation scores, not a full timestamped event archive. Six modes: unconditional gifts, permanent bilateral net-score gate of two units, periodic reset, sliding expiry, linear decay, voluntary release of positive net score. Voluntary release instructions supplied externally, simulated with one-in-eight random chance per consented pair each round; not inferred from need. Sliding/decay integer weights scaled by period. Inherited ten-unit donor ceiling per eight rounds and stock floor one. All allocations verified against offers and claims. Gifts create no obligations. Sequential trusted inputs required; caller records verified actions once. No global optimum or real transfer.

Main/fresh 47001–47012 / 47101–47112: 1008 runs, seven regimes, six modes, period eight. Third cohort 47201–47212: 1092 runs, seven regimes, thirteen policy configurations (reset/sliding/decay at 4/8/16 rounds, unconditional/evidence-limited gifts, permanent, voluntary). 252 fixture/regime combinations, 2100 runs, 252000 rounds, 645830 units allocated. Same exogenous conditions, unequal realized stocks. Timed-abuse inflates claims first two ticks of each eight-tick window. Conservation and lifetime contribution totals verified. No real community data.

Mean unmet units in first two cohorts, 24 runs/cell:
| Regime | Gift | Permanent | Reset | Sliding | Decay | Voluntary |
|---|---:|---:|---:|---:|---:|---:|
| Balanced |0|1.0|0|0.1|0|0|
| Unequal |97.1|555.8|220.4|246.9|102.6|271.6|
| Shock |406.0|749.8|462.8|472.5|408.0|487.1|
| Abuse/mimic |414.2|562.6|312.7|334.0|386.2|368.0|
| Withdraw |282.8|552.6|340.6|359.4|285.1|371.5|
| Timed abuse |298.8|561.3|311.2|332.3|295.2|357.2|

Third cohort selected means, 12 runs/cell:
| Regime | Gift | Verified gift | Permanent | Reset 4 | Reset 8 | Sliding 8 | Decay 8 | Decay 16 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Unequal |74.2|96.4|543.7|85.8|200.3|226.2|80.8|175.6|
| Abuse |415.0|174.3|562.5|345.2|312.1|333.9|386.3|323.6|
| Mimic |415.0|420.1|562.5|345.2|312.1|333.9|386.3|323.6|
| Timed abuse |297.8|299.5|561.8|279.4|311.1|333.1|293.9|297.2|

No universal renewal rule. Excess receipts retained, not necessarily wasted. Simulated behavior and renewal schedules do not establish human motivations or economic sustainability.

Separate signed obligation ledger uses CV1 Ed25519 signatures, SHA-256 event IDs and independently trusted ledger ID/current head/time. Issue requires both parties; release creditor alone; settlement both; pre-agreed expiry reduces outstanding to zero without rewriting history. Reject excessive or expired reductions. No legal effect, actual settlement, clock service, atomic persistence, fork resolution, replay prevention beyond trusted head or transfer of claims. 24 seeds 47401–47424, 12 cases each, 96 valid/192 rejected; 288/288 correct. 48 actual SN1 scans, 144 verified pair checks, reconstructed signed records from CC1 stored bytes before/after expiry. Unchanged archive bytes and mtimes. Temporary stores, deterministic public test keys. Nine tests passed normal/optimized Python, including 100 RC1 permanent equivalence checks and causal prefix invariance.

Core blobs jubilee.py 658806d3da33768b03e8d3ef25f2279357e3d7bc; release.py 9a653fd070319f0b0571acfb9d8dccc913c91979 verified. Complete JUBILEE-047.zip SHA256 f5e3025234564bc134d3904a553932b9edf349c1a11f4a6305ad1475cab1ba12 contains both implementations, inherited modules, tests, benchmarks, raw receipts and logs. Tests/benchmarks not ported this pass. No security audit, remote CI, merge or production activation.
