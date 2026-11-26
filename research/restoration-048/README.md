# RESTORATION 048 — RS1
Research-only Python 3.10+ standard library. Set PYTHONPATH=../reciprocity-046 (POSIX). plan(offers,gaps,projects,accepted,priority,policy='guarded') returns relief unit pairs, at most one fully funded project ID, and funding donor indices. check independently replays consent and combined donor limits. Donor must consent to all beneficiaries; all beneficiaries must accept project; self-funding excluded. Relief assumes submitted gaps imply acceptance. No repayment, execution, signatures, market pricing, labor/maintenance costs, ownership or actual community data. Trusted in-process inputs. Greedy priority is recent gap times nominal yield per cost/delay. Guarded invests only after all current gaps met; relief-first prioritizes immediate relief but may invest while some gaps remain. Productive/shared/hybrid prioritize projects. Identical exogenous conditions, donor floors and eight-round ceilings (10 units), unequal realized expenditure.

Main seeds 48001–48012 / 48101–48112: 1176 runs, seven regimes x seven policies, 100 rounds except short=35. Stress 48201–48212: 420 runs, five regimes, seven policies, 100 rounds except urgent=12. Followup 48301–48312: 420 runs, five regimes x seven configurations. 2016 runs, 175896 rounds, 323496 relief units, 73976 investment units, 747122 gross additional simulated production, 13987 projects started, 10238 completed, 3342 failed, 5484 destroyed after completion, 407 pending. Conservation checked each round. Main personal cost 4/yield 2, shared cost 6/yield 1 per each of three beneficiaries, completion delay 3 (slow=8), 8% failure (failure regime 65%). Durable capacity until staged damage, no ongoing cost. Favorable assumed returns, not empirical estimates. Damage affects installed projects only. Stress raises cost, lowers yield and initial stock, delays or eliminates returns; fragile uses original costs and repeated damage. Followup stops considering a project after two failures or all projects after three consecutive failures until pending success resets streak. Deadline variant adds nominal gross-unit payback gate ONLY when urgent deadline disclosed. Heuristics in harness, not RS1 core. No future outcomes used by planner.

Main mean unmet units, 24 runs/cell:
| Regime | Relief | Productive | Relief-first | Shared | Hybrid | Guarded |
|---|---:|---:|---:|---:|---:|---:|
|Unequal|191.8|1.2|0.6|1.5|2.4|0.8|
|Catastrophe|194.5|2.6|1.0|2.2|3.0|0.8|
|Scarcity|449.3|11.1|14.5|100.4|2.4|0.8|
|Slow|191.8|8.1|7.0|8.2|15.8|10.1|
|Failure|191.8|18.3|23.6|13.7|19.0|25.6|
|Withdraw|365.3|1.2|0.6|1.5|2.4|0.8|
|Short|50.0|1.2|0.6|1.5|2.4|0.8|

Fresh followup means, 12 runs/cell:
| Regime | Relief | Hybrid | Guarded | Hybrid-stop | Guarded-stop | Hybrid-deadline | Guarded-deadline |
|---|---:|---:|---:|---:|---:|---:|---:|
|Costly|214.8|56.4|129.1|56.4|129.1|56.4|129.1|
|Fragile|205.8|66.9|98.4|76.2|102.8|76.2|102.8|
|No return|214.8|497.3|232.8|246.2|232.1|246.2|232.1|
|Tight|720.2|663.8|720.2|663.8|720.2|663.8|720.2|
|Urgent|13.2|39.6|18.5|39.6|18.5|14.1|13.2|

No universal dominance. Stopping rule harms fragile recovery; known-deadline gate helps urgent case. Recipient-turned-donor counts observational, not causal. Nine unit methods passed normal/optimized including 1400 randomized plan checks, causal prefix, quotas, consent, deadline. Physical replay 48501–48548: 48 temporary cases, 96 SN1 scans, 192 object/peer checks, 12 recipes recovered byte-exactly through CW1, 240 deterministic arithmetic outputs matched originals. 12 withheld-consent cases no restore attempted, 12 missing and 12 corrupt source cases failed safely. Donor bytes/mtimes unchanged. Recipe data not executed as code. No real user files, independent hardware or live permissions. No signed execution bridge, security audit, production activation or merge. Source blob 4c9c18f41bf4cbf3866dc298e89ab2036c898e4c verified. Full RESTORATION-048.zip SHA256 55860930f553c5ba2c1c268fd668380dde90e86e9ea2ee7dd5fa40f010161e16 contains implementation, inherited modules, tests, benchmarks, receipts and logs. Tests/benchmarks local package only; remote CI unverified.
