# Codec Invariants — v0.1.2

A candidate is ineligible unless:

1. `decode(encode(x)) == x`
2. `L(c) = 8 * |serialize(c)|`  (engine-measured)

Engine owns measurement. Proposers supply only executable frames.

Additional v0.1.2 gates:

- Signed Int32 contract enforced before any work.
- Canonical (minimal) varints required.
- Canonical mask padding: unused high bits of final mask byte must be zero.
- Resource limits (MAX_SAMPLES_PER_FRAME, MAX_FRAME_BYTES, MAX_PERIOD) checked before allocation.
- Uniform `CodecFormatError` for all wire failures.
- Witness dispositions: NO_PROPOSAL | REJECTED | ELIGIBLE | SELECTED (exactly one SELECTED).
- Deterministic tie-breaker: (emitted_bits, family_id, frame_bytes).

WitnessLedger remains optional for decompression.
