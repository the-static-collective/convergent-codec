# PERCEPTION 032 — PN1 longitudinal evidence

Read-only research instrument. Python 3.10+, standard library. From this directory set PYTHONPATH=../interdependence-026 (POSIX). Use stable trusted local stores and independent manifest pin. No repairs, deletions, live networking, or background service.

```sh
python sensation.py manifest.json PIN --peer desktop=/path/to/store --peer laptop=/path/to/other > first.json
python perception.py manifest.json PIN first.json --sample 8 > plan.json
python sensation.py manifest.json PIN --peer desktop=/path/to/store --peer laptop=/path/to/other --selection plan.json > second.json
python perception.py manifest.json PIN first.json second.json --sample 8 > next-plan.json
```

Default rotation, fixed sample size and manifest, one report per step after initial full scan. Other policies: random, age, adaptive. Ledger preserves latest observation and last decisive evidence separately; logs observed transitions by gap and joint peer-root states. Counts not calibrated probabilities. Hash chain commits to ordered report hashes; not authenticated. Operator supplies chronological reports and stable labels. Ledger currently accepts direct SN1 reports only, not parity-record reports. Observer retains parity capabilities.

40 local sequences (six main and four fresh seeds per each of four regimes), 24 steps, 36 objects, four peers, six sampled identities per step. 3840 sampled reports, 92160 sampled pair observations matched full scans. 661 corruption episodes; random detected 365, rotation 510, age 509, adaptive 476. Sampled read bytes respectively 7345496, 7300203, 7298788, 6891392; initial and truth scans excluded. Equal probes, unequal bytes; tiny corrupted payloads can make revisiting faults appear cheaper. Fresh recurring adaptive 66/75 detected, mean conditional delay 1.79 ticks; rotation 69/75, 2.42 ticks. Fresh dispersed 79/95 vs 89/95; fresh brief 52/96 vs 47/96. All policies recognized 60 inaccessible peer-ticks, no false wipe alerts in these staged fixtures. Rotation max evidence age 5 on continuously accessible corruption workloads, adaptive 7–9, random 23–24. Adaptive remains optional; not a universal improvement. Missing-copy alert is not a proven causal explanation or permanent loss. No actual user machine observations.

Eight local unit methods pass normal and optimized Python; CLI full scan to ledger to directed scan and back passed. Upstream verified blobs perception.py bf1b1a4085a5bc0cde27706414c3b36eb60d2f91, sensation.py 2cd9e6e14c494da2d5421d7b370a8f21b528a88a. Complete downloadable PERCEPTION-032.zip SHA256 0337a4bfb36d503bf1fb6e427c17bafd343c2bb35c42d3c09d19e8090e048b5f includes inherited modules, tests, benchmark, results and logs. Tests/benchmark not ported this pass; no remote CI verified, network deadlines, security audit or production activation. Draft PR only.
