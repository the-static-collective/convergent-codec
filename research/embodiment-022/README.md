# EMBODIMENT 022 — EC1

Experimental standalone implementation under the existing ORGANISM draft PR. Not compatible with OR1 or the original Int32 frame. Python 3.10+, standard library only at runtime.

Install from this directory: `python -m pip install .`. Commands: `convergent-ec1 compress input.bin output.ec1 --witness witness.json`, `convergent-ec1 inspect output.ec1`, `convergent-ec1 decompress output.ec1 recovered.bin`, `convergent-ec1 benchmark input.bin`.

EC1 is little endian: magic EC1 followed by NUL, u32 record count; each record has u8 mode, u32 source length, u32 payload length, 32-byte source SHA-256, payload. Modes 0 raw, 1 independent DEFLATE, 2 rolling raw DEFLATE, 3 normalized DEFLATE, 4 rolling normalized DEFLATE. The normalized representation has two u32-length-prefixed byte strings: skeleton and identifier table (itself length-prefixed entries). Skeleton NUL followed by u16 index substitutes table bytes. Histories are last 32 KiB of decoded bytes or transmitted normalized representations respectively. Decoder requires no tokenizer or external history. Bounded to 1024 records, 64 KiB per record, 256 KiB inflated representation, 64 MiB total output. Explicit validation, not assertions, enforces the frame contract. Digests are integrity checks, not authentication.

The original local greedy mode failed to bootstrap normalized history. The amended encoder compares complete raw-only, greedy structural and seed-enabled structural streams, including every byte of speculative seed overhead. No external history or OR1 regional retrieval, patching or grammar mechanisms have been ported yet.

## Local benchmark (Python 3.13.5, zlib 1.3.1)

| Workload | Blocks | Source bytes | Rolling baseline | EC1 | Best offline control |
|---|---:|---:|---:|---:|---:|
| Renamed functions | 80 | 109600 | 15527 | 8576 | 4608 |
| Real stdlib | 5 | 189773 | 45765 | 45765 | 40222 |
| Random binary | 40 | 81920 | 83568 | 83568 | 82113 |
| Mixed | 80 | 136720 | 91375 | 87915 | 86164 |

Initial local greedy implementation tied the rolling baseline on all four. The amended results use the same corpus, post hoc. All eight final API streams reconstructed exactly. Offline controls compress length-prefixed blocks without EC1 per-record integrity metadata; they have future access and are not wire-format matched. CLI uses fixed 64 KiB chunks; benchmark API uses document boundaries. Real stdlib corpus depends on local Python installation. No universal advantage. Encoding time increased (renamed 0.0205 to 0.1091 s, single run).

Local 14 test methods passed in normal and optimized Python; includes 1000 random malformed frames, 500 structured mutations, truncation and bomb checks. A clean venv installation and all four CLI commands succeeded. Six source/package/test/benchmark files on this branch were checked against local Git blob hashes and matched. CI workflow added; remote CI results not yet verified. No production release, merge, security audit or claimed hard RAM limit.

Local distributable wheel SHA-256: 20c3b35d6c6965016b9b418d5e6f323af2833978c9f28711276550f075523925.
Research zip SHA-256: a837318b93d2be87bd778e5bd9b6952ecc1b4d959b782669422b919a10692cca.
These binaries are separately delivered, not uploaded to GitHub.

Reproduce: `python -m unittest discover -s tests -v`, `python -O -m unittest discover -s tests -v`, `python benchmark.py`.
