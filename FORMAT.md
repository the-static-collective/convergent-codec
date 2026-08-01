# Frame Formats

## Common Header (all families)

- version: u8 (currently 1)
- family: u8  (0 = RAW, 1 = PERIODIC_SPARSE)
- sample_count: uvarint
- source_sha256: 32 bytes

## Family 0 — RAW

```
version
family = 0
sample_count
zigzag-varint values (exactly sample_count)
source_sha256
```

Reconstruction: the zigzag-varint stream is the source.

## Family 1 — PERIODIC_SPARSE

```
version
family = 1
sample_count
period: uvarint
amplitude: zigzag-varint   (integer amplitude)
phase: uvarint
generator_version: u8
anomaly_mask: bit-packed (ceil(sample_count/8) bytes)
anomaly_values: zigzag-varint stream for each set bit (in order)
ordinary_residual: zigzag-varint stream for every sample
source_sha256
```

Reconstruction equation (exact, integer arithmetic only):

```
x_i = g(i; θ) + a_i + r_i
```

where

- `g` is the deterministic integer periodic generator
- `a_i` is the explicitly encoded sparse anomaly (0 when mask bit clear)
- `r_i` is the ordinary residual (never silently zeroed)

Nothing is omitted. Every sample is fully specified.
