"""Declared format resource limits. Part of the public contract."""

MAX_FRAME_BYTES = 1 << 20          # 1 MiB
MAX_SAMPLES_PER_FRAME = 1 << 16    # 65 536
MAX_PERIOD = 1 << 15               # 32 768
MAX_MASK_BYTES = (MAX_SAMPLES_PER_FRAME + 7) // 8
