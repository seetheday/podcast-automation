from array import array

import pytest

from automation.edit.meter import integrated_lufs, true_peak_dbfs


def test_true_peak_dbfs_handles_silence() -> None:
    assert true_peak_dbfs(array("h")) == float("-inf")


def test_true_peak_dbfs_returns_zero_dbfs_for_full_scale() -> None:
    samples = array("h", [32767, -32767])
    assert true_peak_dbfs(samples) == pytest.approx(0.0, abs=0.05)


def test_integrated_lufs_matches_simple_rms() -> None:
    samples = array("h", [16384] * 100)
    loudness = integrated_lufs(samples)
    assert loudness == pytest.approx(-6.69, abs=0.1)
