# INTERDEPENDENCE 026 — ID1

Local experimental GF(256) erasure recovery over independently pinned CC1 manifests, with XOR as the all-ones coefficient case. Polynomial 0x11d. Bounded RREF (128 variables, 128 rows, 8 terms, 16 KiB object). Recovers uniquely determined variables even when full rank is absent. Checks exact lengths, zero padding, SHA-256. Corrupted parity is ignored, inconsistent equations fail closed. Existing formats unchanged. No network or production deployment.

Python 3.10+, standard library only. Run interdependence.py --help. The protect command writes one equation list using HASH:COEFFICIENT arguments; assemble multiple records with the API. Recover using manifest, independently obtained manifest pin, equations JSON, independent equation pin, local cache, new destination, peer stores. Exit 3 indicates incomplete recovery. No deletion.

Three-file actual recovery from only three XOR equations: peeling 0/3, linear 3/3, same 21 reads and 5003 encoded read bytes. Twelve local test methods passed both normal and optimized Python. Local source Git blob 9c429f93add6308091e67ece0bd8bff0e4c85589 matches ported implementation.

Synthetic: 6 seeds, 48 singleton objects, 6 peers, equal or variable sizes, 25% and 55% protection ceilings. Budget includes encoded protection and equation JSON, excludes common metadata, transport and filesystem overhead. At 55% ceiling, missing-object instances over 90 double outages:
| Strategy | Equal | Variable |
|---|---:|---:|
| Replication | 816 | 476 |
| Single XOR | 1152 | 1152 |
| Two parity GF(256), peeling | 984 | 996 |
| Same equations, linear | 480 | 528 |
| Binary overlap, linear | 822 | 463 |

At 55%, single XOR and two parity both recover all 36 single outages per size regime. No complete two-peer recovery at those synthetic budgets. Variable-size replication is stronger than GF(256) stripes for some larger outages. Availability modeled by algebraic rank, not physical restore. Simple systematic two-parity stripes use first row all ones and second distinct nonzero coefficients, an MDS two-erasure construction; not a production RS library benchmark.

Real-source directory: 273305 bytes, 27 objects. Initial planner left three unprotected tail objects (3/6 single, 3/15 double complete). Tail-safe posthoc repair groups remaining distinct owners in smaller stripes. Final 14 equations cost 161141 bytes including metadata against 126755 encoded original payload (127.1%). Actual 6/6 single and 15/15 double outage restores exact; 0/2 selected triple losses. Not a matched-budget comparison, only one real fixture.

Complete benchmark, tests, initial and final results in separate INTERDEPENDENCE-026.zip, SHA256 27b4056fa7f699bba444c5da399da70065310ed7193f6f3fe5230c618418656d. Tests and benchmark not ported upstream this pass. No remote CI verified. No security audit, authenticated transport, concurrency safety or hard RAM guarantee. No novel erasure code claim. Draft PR only.
