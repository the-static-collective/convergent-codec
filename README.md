Convergent Model Compression

Convergent Model Compression is an experimental exact codec architecture that searches for shared structural generators across independently proposed models.

The core rule is strict:

«A candidate may compete only if its emitted frame deterministically reconstructs the exact source sequence, and its cost is measured from the actual serialized bytes.»

This repository contains the first lawful kernel of that idea.

It currently supports signed 32-bit integer sequences through two frame families:

- RAW — universal exact fallback
- PERIODIC_SPARSE — deterministic integer periodic generator plus explicit sparse anomalies and residuals

The encoder evaluates candidate frames, rejects anything that fails exact reconstruction, and selects the smallest valid emitted frame.

---

Core invariant

For every eligible candidate:

decode(encode(x)) == x

And its description length is:

exact_bits = len(serialized_frame) * 8

No estimated metadata costs.

No lossy residuals.

No hidden decoder state.

No model may claim a saving that its own frame cannot demonstrate.

---

Why this exists

Most compression systems choose one modeling language:

- dictionaries
- transforms
- recurrence
- entropy prediction
- grammar
- neural latent spaces

This project investigates a narrower question:

«Can independently fitted model families expose a shared exact-cost artifact that can be serialized once and reused?»

Examples include:

- shared parameters
- shared structural templates
- shared anomaly locations
- shared event masks across multiple channels

The project calls such intersections crossroads.

A crossroads is not a block with many interesting descriptions.

It is a block where independently derived descriptions expose a common generator that is cheaper to encode than the competing descriptions separately.

---

Current status

Version: 0.1.2

The current kernel provides:

- exact signed "Int32" reconstruction
- canonical ZigZag varints
- canonical bit-mask padding
- deterministic integer-only periodic generation
- explicit sparse anomaly values
- explicit residual streams
- SHA-256 reconstruction verification
- engine-owned emitted-bit accounting
- deterministic candidate tie-breaking
- strict malformed-frame rejection
- decoder resource limits
- optional witness-ledger decision lineage

The current test suite contains 21 passing tests.

This is a research prototype, not a production compression library.

---

Architecture

The system separates three concerns.

1. Payload plane

Contains only what the decoder needs to reconstruct the source exactly.

The witness ledger is never required for decompression.

2. Model sandbox

Model families independently propose executable candidate frames.

A proposal cannot directly control its measured cost. The engine calculates:

exact_bits = len(frame) * 8

The engine then decodes the frame and verifies exact identity before allowing it to compete.

3. Witness plane

Records decision lineage without contaminating the compressed payload.

Each proposal receives one disposition:

NO_PROPOSAL
REJECTED
ELIGIBLE
SELECTED

Exactly one eligible candidate becomes "SELECTED".

---

Frame families

RAW

The universal baseline.

version
family
sample_count
zigzag-varint values
source_sha256

RAW is always proposed and provides the upper bound for candidate selection.

The selected frame can therefore never be larger than the emitted RAW frame among the currently implemented candidates.

PERIODIC_SPARSE

Models a sequence as:

x[i] = generator(i, parameters) + anomaly[i] + residual[i]

The frame contains:

version
family
sample_count
period
amplitude
phase
generator_version
residual_mode
anomaly_mask
anomaly_values
residual_stream
source_sha256

The current generator is a deterministic integer square wave.

No floating-point arithmetic is required during decoding.

---

Installation

Clone the repository:

git clone https://github.com/the-static-collective/convergent-codec.git
cd convergent-codec

Install locally:

python -m pip install .

Install with test dependencies:

python -m pip install ".[test]"

Run the test suite:

python -m pytest

---

Quick start

from convergent_codec import encode, decode, WitnessLedger

source = [
    10, 10, 10, 10,
    -10, -10, -10, -10,
] * 8

ledger = WitnessLedger()

candidate = encode(source, ledger=ledger)
recovered = decode(candidate.frame)

assert recovered == source

print(candidate.family)
print(candidate.exact_bits)
print(ledger.to_dict())

---

Exactness and format rules

The public format contract currently enforces:

MIN_SAMPLE = -2^31
MAX_SAMPLE =  2^31 - 1
MAX_SAMPLES_PER_FRAME = 65,536
MAX_FRAME_BYTES = 1 MiB
MAX_PERIOD = 32,768

Frames fail closed on:

- unknown format versions
- unknown model families
- unknown generator versions
- malformed varints
- non-minimal varints
- truncated frames
- trailing bytes
- invalid mask padding
- excessive sample counts
- excessive frame sizes
- excessive periods
- reconstruction digest mismatch
- reconstructed values outside signed "Int32"

The candidate tie-breaker is deterministic:

(emitted_bits, family_id, frame_bytes)

---

Repository layout

convergent-codec/
├── convergent_codec/
│   ├── canonical.py
│   ├── decoder.py
│   ├── engine.py
│   ├── errors.py
│   ├── frames.py
│   ├── generators.py
│   ├── limits.py
│   ├── varint.py
│   ├── witness.py
│   └── models/
│       ├── raw.py
│       └── periodic_sparse.py
├── tests/
│   ├── test_candidate_selection.py
│   ├── test_malformed_frames.py
│   ├── test_periodic_sparse_roundtrip.py
│   ├── test_raw_roundtrip.py
│   └── test_varint.py
├── FORMAT.md
├── INVARIANTS.md
└── pyproject.toml

---

What is novel here

Model selection is not new.

Minimum Description Length is not new.

Predictor mixing is not new.

The distinct research target is:

«Explicitly mine convergence between heterogeneous model families for shared exact-cost artifacts.»

Three convergence classes are especially relevant.

Parameter convergence

Different detectors independently infer the same parameter.

Example:

spectral detector → period 24
autocorrelation detector → lag 24
event timing detector → cycle 24

The parameter is encoded once.

Structural convergence

Different representations identify the same reusable object.

Example:

token phrase
AST subtree
dependency motif

All may expose one canonical function template.

Residual convergence

Different models fail at the same positions.

Those shared failure locations may indicate a second sparse process rather than unrelated noise.

This is the most practical immediate research direction.

---

Next research slice

The next major experiment is multichannel shared-mask compression.

For channels "j":

x[j][i] = g[j](i, parameters[j])
        + mask[i] * anomaly[j][i]
        + residual[j][i]

The shared event mask is encoded once.

Channel-specific generators, anomaly magnitudes, and residuals remain separate.

The experiment compares:

L(shared mask + channel values)

against:

sum(L(independent mask per channel))

A positive result requires full emitted-byte accounting and exact reconstruction for every channel.

Detection alone is not success.

Only a shorter valid serialized frame is success.

---

Non-goals

This project does not currently claim to:

- outperform "zstd" on arbitrary files
- compress random data
- infer metaphysically true latent causes
- provide cryptographic authenticity
- provide production-ready hostile-input security
- replace general-purpose codecs
- treat external catalogs as free decoder side information

The witness ledger records reproducible decision lineage.

It does not prove that the selected model is the only valid interpretation of the data.

---

Design boundary

The central distinction is:

«Compression correctness is exact reconstruction.
Witness correctness is reproducible decision lineage.»

The payload proves that a specified decoder reconstructs specified values.

The witness ledger records:

- which models proposed frames
- which proposals failed
- emitted frame lengths
- candidate frame hashes
- model evidence
- the deterministic selection result

The witness layer remains optional for decoding.

---

Project thesis

The current working thesis is:

«When independently derived models repeatedly share parameters, structures, anomaly locations, or generators, their common artifact can sometimes be encoded once, producing a shorter exact description than any model can produce independently.»

This repository exists to test that thesis without allowing metaphor, model confidence, or attractive structure to impersonate measured compression.
