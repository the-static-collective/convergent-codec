"""Stable codec exceptions."""


class CodecFormatError(ValueError):
    """Malformed, truncated, unsupported, non-canonical, or out-of-range codec frame / input."""
    pass
