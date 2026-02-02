"""Simplified loudness metering utilities for the edit stage."""

from __future__ import annotations

import math
from array import array

_FULL_SCALE = 32768.0
_BS1770_OFFSET = -0.691  # Approximate offset for LUFS conversion


def integrated_lufs(samples: array) -> float:
    """Compute a simple BS.1770-style integrated LUFS measurement."""
    if not samples:
        return float("-inf")

    mean_square = sum((sample / _FULL_SCALE) ** 2 for sample in samples) / len(samples)
    if mean_square <= 0:
        return float("-inf")
    return 10 * math.log10(mean_square) + _BS1770_OFFSET


def true_peak_dbfs(samples: array) -> float:
    """Compute the maximum sample peak in dBFS."""
    if not samples:
        return float("-inf")

    peak = max(abs(sample) for sample in samples) / _FULL_SCALE
    if peak <= 0:
        return float("-inf")
    return 20 * math.log10(peak)
