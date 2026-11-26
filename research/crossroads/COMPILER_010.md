# CROSSROADS 010 — The Compiler of Knowledge

Historical 010 documentation: the public 012 overlay deliberately excludes the raw `lineage/` archive. Commands and earlier measurements below refer to 010.

A local, inspectable research runtime assembled from Crossroads 005/008/009, carrying the complete earlier research artifacts in `lineage/`. Standard Python 3.10+, no third-party packages. Tested with Python 3.13.5. Not a production codec or an arbitrary code learning engine. No network, automatic canon admission, external writes or account connection.

## Start

Extract the ZIP, open a terminal in its directory, and run:

```
python compiler.py init my_state.json
python compiler.py compile my_state.json demo_output/inherited/request-0.json my_artifacts
python compiler.py inspect my_state.json
python compiler.py verify my_state.json my_artifacts
```

Windows may use `py -3` in place of `python`. `init --cold` starts with length only. Commands print JSON. Do not initialize over an existing state. Use separate state directories for different experiments. One writer at a time; no concurrent locking. An interrupted write may leave an unreferenced content-addressed artifact; the state is atomically replaced after the artifact is written. Back up state and artifacts together.

`compile` accepts a JSON object with `name`, `source`, and `train`, `validate`, `target`, each a mapping of `inputs` (nonempty lists of integer sequences, length 1–8, values -32..32) and `outputs` (one signed magnitude < 2^63 integer per sequence). Up to 256 samples per bank. Input banks must not overlap across splits. Example request files are bundled. This is an observed-output compiler, not a service that predicts unknown future events. Target output values must be supplied to encode residuals; candidate selection and admission never use those outputs. The target's exact prediction count is reported separately. The target input bank is explicit decoder context.

To export a compact self-contained transport package (within the frozen VM specification), use the artifact ID printed by `compile`:

```
python compiler.py pack my_artifacts/ARTIFACT_ID.json result.cp1
python compiler.py unpack result.cp1
```

The binary CP1 package contains a compressed input context plus a GE1 output frame, with SHA-256 output and input-context checks. The decoder requires this project's fixed VM implementation but no learned state, calibration data or audit history. The artifact JSON is an audit object and deliberately duplicates observations; it is not a compact archive. `decode` accepts the JSON artifact directly. `inspect` displays the active/dormant catalog, observed usage and savings. `verify` recomputes all decisions and checks both output and baseline frames against the stored observations. Hash chains detect corruption against a trusted state, not authenticity or malicious rewriting of the entire history.

## Reproduce

```
python -m unittest -v test_compiler
python demo.py
python compiler.py verify demo_output/inherited/state.json demo_output/inherited/artifacts
```

`demo.py` replaces its own named demo states and writes deterministic results; don't put private data there. Eight unit/integration tests cover context and digest tampering, journal and artifact tampering, independent validation, disjoint banks, target-output independence, compact transport, and fresh-process CLI replay. Four policy arms, six encounters each, 1,536 target observations across all arms. All 24 output frames and 24 baseline frames round-trip. Inherited learning: 540 output bytes, 8,737 vector candidate evaluations, five completely predicted encounters, three admissions. Inherited no learning: 540 bytes, 12,390 evaluations, five complete, zero admissions. Cold: 1,012 bytes, 6,504 evaluations, zero complete. Frozen inherited without composition: 1,012 bytes, 156 evaluations, zero complete. The cold and frozen results are for this staged policy, not a proof that larger searches cannot discover the targets. Candidate counts are not elapsed time.

Context-inclusive CP1 packages: 2,522 B learned vs 2,994 B fallback. Calibration separately costs 2,477 B compressed, common to all demo arms. Thus charging calibration against plain storage makes the compiler more expensive on this short run. Persistent learning state is 4,439 B; six full JSON audit artifacts are 20,732 B. Initial Genesis provenance and prior donor acquisition costs are separate. No claim of end-to-end storage advantage. The 21 eligible expressions after replay occupy 101 B in the inherited CK1 DAG format, separate from the audit journal.

## Policy and lineage

- 41 historical expressions and exact provenance preserved in `catalog.json`; 18 expressions from the previously selected sign-closed inheritance lineage are eligible initially. No automatic admission of all historical candidates. This is an experimental local eligibility policy, not a reviewed Collective canon decision.
- Active limit 8, ordered by prior modeled use, savings, then bytecode; dormant candidates retained. If active fails exact training match, scan the archive; if still not exact, compose from atom roots and retained parents. Stop or fail closed on the fixed pool limit. Candidate scoring uses serialized residual-plus-definition bytes on training; symbolic quotient uses exact integer ring identities over opaque atoms. Only train-exact, validation-exact, validation-wire-saving candidates are admitted, maximum 64 eligible expressions. No automatic search if an existing candidate fits train but fails validation; it falls back. Future work: discriminating probe invention, improved escalation, measurement of actual elapsed compute, recursive fertility and per-primitive marginal attribution. Usage savings are attributed to the selected model, not causal marginal savings.
- `living.py`, `genesis.py`, `conservation.py` are recovered source from 009. `compiler.py` is the new orchestration/GE1 decoder; `demo.py` and tests are new. `proof_witnesses.json` preserves prior symbolic witnesses. `lineage/` includes the nine prior stages, with a SHA-256 inventory. The 001–004 event/AST/behavior/probe engines are archived research, not live adapters in this runtime; 006–007 policies and donor vocabulary informed the seed, not a direct integration of their code. `conservation.py`'s original standalone demo requires its original archive, not the new runtime. No actual HUMKIN ingestion, MEMENTO native connector or MOTIF service integration yet. No GitHub modifications.
- Bounded integer grammar, synthetic, deliberately related targets. The one weighted-sum control remains unresolved. This is a local trusted-input research program, not hardened against hostile data. Imported legacy research modules include assertion-based checks and unbounded standalone legacy decoders; only the new CLI uses explicit bounded GE1/CP1 decode checks. Never run unknown code extracted from research sources. State must be treated as private if inputs are private.
