# ORGANISM 021 — Integrated reconstruction architecture

Status: research receipt; runtime integration held. 2026-11-26.

This records the locally executed OR1 experiment, not a new production frame family. The implementation is distributed in the separate ORGANISM-021 research package. The existing exact Int32 frame contract remains unchanged.

## Frozen benchmark

Two fresh seeds (2120, 2121) for each of regular, partial, fragmented, mutated, novel and mixed source/binary streams; one fresh standard-library function stream (21021). Each has 24 pre-shared historical documents, 8 training documents and 16 held-out documents. 13 streams, 208 held-out documents.

All 10 integrated configurations reconstructed each held-out stream exactly. Frames include per-document SHA-256, framing, mode flags, references, paid grammar definitions and a historical archive digest when applicable. No model can claim savings from a failed reconstruction. The experimental decoder is for trusted research fixtures only.

| Configuration | Emitted bytes |
|---|---:|
| Independent conventional | 57819 |
| Rolling conventional | 56300 |
| Normalization + rolling | 44174 |
| Historical raw + rolling | 56096 |
| Whole-artifact attention (core without regional) | 37197 |
| Single-source (best compact patch among three retrieved sources, plus individual dictionaries) | 42379 |
| Core without explicit patch | 36679 |
| Core without rolling | 37602 |
| Core | 34879 |
| Core + learned grammar | 34832 |

The core uses reversible identifier normalization, compact regional retrieval, multiple-source copy/literal patches, conventional compression and synchronized rolling representations. Grammar contributes 47 bytes of marginal savings and is admitted on training data only; measured aggregate encoding time increases from 1.059 to 3.974 seconds, including grammar training. Single-run timing is not a latency guarantee.

## History is not free

Compressed historical storage totals 46756 bytes across the 13 independent streams. With history already independently retained, core payload beats raw rolling by 38.0%. If purchased solely for these streams, core plus history costs 81635 bytes; standalone normalization with rolling costs 44174 bytes. A training-only architecture router selected standalone normalization in all 13 streams when charged for historical storage, and selected history-enabled modes when history was pre-shared (34878 emitted bytes).

The matched-history offline control is substantially stronger than the sequential core. No universal compression advantage is claimed.

## Admission decisions

- Retain exact reconstruction, emitted cost, digest and raw fallback as mandatory laws.
- Candidate core for source streams: reversible normalization, compact regional retrieval, explicit multi-source patches, rolling conventional compression. Require explicit historical dependency and digest.
- Conditional organ: train-admitted grammar; do not enable by default. Retain conventional compression as an eligible candidate.
- Research-only: integer lineage discovery, historical provenance, learned search and budget allocation, finite memory and historical witness recovery. Their earlier results are not revalidated by this test.
- Preserve negative evidence: offline compression remains stronger; history can cost more than its dividend; additional grammar complexity may not justify its small benefit.
- Do not merge experimental OR1 into v0.1.2 Int32 decoder. Next integration requires checked frame bounds, explicit errors rather than assertions, versioned deterministic tokenizer, resource-limited decoder, hostile-input tests, pinned corpus, dependency lock and CI.

The local clone was blocked by DNS resolution. This branch intentionally records findings and integration gates, not a claim that the local runtime has been ported or upstream tests run.
