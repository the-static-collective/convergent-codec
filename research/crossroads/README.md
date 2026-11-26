# Crossroads — Sensory Frontier & Embodiment

**Experimental research overlay for `the-static-collective/convergent-codec`.**
Review branch: `research/crossroads-012-embodiment`. Inspected base: `38ede773ace9a38e27c61e159c36cda17090ca16`. This overlay does not alter the existing Int32 codec, dependencies, wire format, or production entry points. GE1/CP1 are separate experimental formats. No merge or activation is implied.

## Reproduce

From `research/crossroads/` (Python 3.10+, standard library):

```
python sensory.py
python -m unittest -q
python compiler.py inspect evidence/persistent/state.json
python compiler.py verify evidence/persistent/state.json evidence/persistent/artifacts
```

The eight inherited tests pass on Python 3.13.5. The sensory run was repeated, with identical results and SHA-256 `fabf5652d949b59a5de9228c3b608d09b353e66a85ecb70587d5b0f3f7f2cc87` for `evidence/results.json` on that interpreter. AST results may vary with Python versions. The compiler is a trusted local research tool, not a hardened untrusted-input service.

## Observations and results

The AST excerpts are from three pinned public repositories (see `sources/PROVENANCE.txt`). Their 1,451 AST nodes give 787 eligible non-leaf nodes with 1–8 children and child degrees <=32. To meet the compiler's disjoint input rule, 493 nodes with previously encountered input vectors are excluded from the later partitions. The resulting 213/52/29 training/validation/test examples have 43/19/25 unique contexts respectively. This is a novel-context test, not representative coverage of all nodes. Multiple observations with identical contexts within a partition are retained. No donor code executed.

`jarvis_commits.tsv` records 45 public GitHub connector-returned timestamps and 12-character commit prefixes (not full SHAs), November 6–26 UTC. Observed intervals are rounded to half-hour units and capped at 32; split 15/15/14 intervals before generating overlapping three-lag contexts. One later duplicate context excluded, yielding 12/12/10 observations. These bounded results are not a complete event stream. Scheduled activity is not removed. No actual audio or native MOTIF research graphs were accessed.

| Task | Baseline output bytes | Compiled bytes | Validated exact predictions |
|---|---:|---:|---:|
| Grandchildren count (positive control; known sum identity) | 98 | 73 | 29/29 |
| Full descendant count given child degrees | 100 | 100 | 0/29 |
| Next observed commit interval | 79 | 79 | 0/10 |
| Total | 277 | 252 | 29/68 |

All 9 frames across persistent/frozen/cold modes reconstructed exactly, all 9 portable packages round-tripped, and all three journals replayed. Persistent 4,138 candidate evaluations; frozen 60; cold 3,256. All produce the same 252-byte total; cold admits sum, others already have it. Calibration costs 1,303 bytes; portable totals are 528 vs 553 bytes (context included), excluding calibration and journal. No new primitive admitted by persistent run. No forecasting advantage established. Simple sum is a perfect baseline for the positive control. Median baseline has one exact commit-gap prediction; compiler abstains. Two held-out AST contexts have conflicting descendant labels: `(6,)` -> 9 and 14; `(2,1,1)` -> 10 and 14. Thus exact deterministic prediction of full descendants from these features alone is impossible on this fixture. Missing context is not evidence of a new useful primitive.

## Ownership and boundaries

The original codec owns the exact-cost research and expression engine. MOTIF is a potential discriminating-probe client; MEMENTO a potential read-only historical observation client; GRAFT a candidate transplant client. No integrations are activated. No private MEMENTO observations or previous raw lineage archives are bundled here. Earlier locally held artifact: `crossroads_010_knowledge_compiler.zip`, SHA-256 `2dcc7dd3f38e775ad99f3f408404dcd4480485422498ae1515447c626ec082fe`. `catalog.json` and `proof_witnesses.json` retain the synthetic Genesis evidence used by the runtime. Review provenance and publication scope before pushing to the public repository. No native codec tests were run in this overlay; no claims about native runtime correctness are made.

## Proposed placement

Unzip this overlay at the root of a clone of the inspected repository, on a new research branch, then run the commands above. Review files with `git status` and `git diff --no-index /dev/null research/crossroads/README.md`. Only after review and explicit publication approval, stage `research/crossroads/` and open a draft pull request. Do not merge or activate automatically. Historical 010 usage instructions are in `COMPILER_010.md`; its mentions of complete archived lineage refer to the original local 010 artifact, not this overlay.

## Crossroads 012 — Embodiment

The research compiler now offers a calibration-only observational collision detector (`sufficiency.py`). Identical input vectors with different outputs refute exact deterministic representation using those vectors alone. They do not establish the reason: omitted variables, stochasticity, timing, or inconsistent source records remain alternatives. Lack of observed collisions proves neither sufficiency nor generalization.

Run `python -m unittest -q` and `python embodiment.py` from this directory. The paired test uses the same initial inherited catalog for each task and both policies. Descendant-count search drops from 2,065 evaluations to zero; its exact 100-byte literal frame is unchanged. The other tasks are unchanged (8 and 2,065 evaluations; 73 and 79 bytes). The new journal replays three encounters and the three frozen 011 journals still replay. The result file is `embodiment_results.json`. This is an evaluation-count result, not a runtime or storage improvement including audits.

New CLI `compile` calls enable the preflight by default; `--legacy-search` selects the earlier policy. Direct Python `fit` and `compile_file` callers opt in with `sufficiency=True`. This preserves old artifact replay. Each new artifact includes exact collision input vectors, distinct output values, first witness row indices, counts, disposition and proposed next inquiry. Validation is used to stop an impossible search, not to rank candidates. Target outputs do not participate in routing or model selection. Candidate budgets are bounded by the pre-existing pool policy; a budget failure is not proof of an inexpressible target.

Research-only scope: no production changes, private MEMENTO observations, credentials, private messages, or original raw lineage archives. The included catalog records synthetic expression lineage. The original codec remains unchanged. The compiler is for trusted local research input; no security audit, audio integration, causal inference or general intelligence claim.
