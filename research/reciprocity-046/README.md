# RECIPROCITY 046 — RC1
Research-only Python 3.10+, journal requires cryptography>=40 and CV1. Set PYTHONPATH=../covenant-044:../telos-043. Plan-only integer consumable allocation: donor stock, floor, cap and exact permitted recipients; claimed needs; optional evidence cap. Greedy fraction-served priority. Strict direct/indirect credit gates are illustrative net-contribution limits of two units, not all forms of reciprocity. Gifts create no enforceable debt. Reserve adds two units beyond offered floor. Ten-unit voluntary donor ceiling per eight-round window in experiments. Followup resets credit each eight rounds or caps receipts at ten per window. Every allocation independently checked against offer and claim; no global optimum or proof of evidence correctness.

Signed journal reuses CV1 signatures and FL1 exact assent principle. Trusted roster, current checkpoint, stock, observation pin and consent external. Affected donor/recipient keys sign exact batch/frame. Receipt returns next checkpoint with cumulative outflow and prior receipt hash. External atomic single-writer persistence required; old checkpoint/fork reuse not prevented by pure function. No actual transfer, positive duty, debt, asset-specific title, independent claim authentication, security audit or production activation. No verification of chosen allocation policy by journal.

Main/fresh 46001–46012/46101–46112: 1008 runs, six regimes, seven policies. Followup 46201–46212: 648 runs, six regimes, nine policies. 216 fixture/regime combinations, 1656 runs, 198720 rounds, 382177 simulated units allocated. Conservation checked each round. Equal exogenous conditions and offer rules, unequal realized stocks/spend. Synthetic evidence is noisy true gap, contaminated with inflated claims in mimic regime. Excess receipts retained, not necessarily wasted. No real community data or behavioral sustainability guarantee.

Main mean unmet units, 24 runs/cell:
| Regime | None | Gift | Direct | Indirect | Reserve | Verified | Verified-reserve |
|---|---:|---:|---:|---:|---:|---:|---:|
| Balanced |17.0|0.0|2.4|11.1|0.0|3.2|3.1|
| Unequal |577.2|86.9|545.7|569.6|88.4|105.6|106.2|
| Shock |772.7|396.1|741.7|762.7|400.8|405.7|410.0|
| Abuse |570.8|408.0|555.6|563.6|405.5|168.0|168.1|
| Mimic |570.8|408.0|555.6|563.6|405.5|413.1|410.6|
| Withdraw |584.9|287.4|553.7|577.2|288.1|293.5|293.7|

Fresh mean unmet units, 12 runs/cell:
| Regime | Gift | Verified | Rolling direct | Rolling indirect | Capped gift | Capped verified |
|---|---:|---:|---:|---:|---:|---:|
| Balanced|1.8|5.0|1.8|8.2|1.8|5.0|
| Unequal|92.6|110.8|215.8|493.0|155.7|172.0|
| Shock|407.7|413.3|464.2|668.8|433.1|439.7|
| Abuse|416.2|176.4|314.2|488.8|394.0|187.1|
| Mimic|416.2|421.2|314.2|488.8|394.0|399.0|
| Withdraw|290.8|298.8|349.8|503.0|309.6|314.9|

No universal dominance. Credit gates suppress persistent assistance, rolling direct mitigates abuse even under mimic but suppresses honest need. Evidence gating helps only with informative evidence. Extra buffer has no general benefit. Eight tests normal/optimized, 2100 random policy checks, causal prefix, cumulative quotas and signatures. Physical replay 46401–46424: 24 signed staged batches, 49 units represented by unique CC1 objects, 48 SN1 scans/864 pair checks, all expected layouts matched. 24 stale-checkpoint and 24 changed-observation rejections. Before stores unchanged, final layouts separate, same filesystem. No real user devices or actual transfers.

Verified core blobs e8ff303fd7fb0a2c8af441bac944453cb88e2578 and db1a371addcb4816f7fea89a1d03681166455599. Complete RECIPROCITY-046.zip SHA256 c1ef2270e9761f29e1842fc0377a792cb9fdac8db3188f4746cafb07d4da8752 contains tests, benchmarks, inherited modules, raw results and logs. Tests and benchmarks not ported this pass; remote CI not verified. Draft PR only.
