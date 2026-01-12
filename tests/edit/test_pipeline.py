"""Tests for the edit stage pipeline helpers."""

from __future__ import annotations

import wave
from array import array
from pathlib import Path

import pytest

from automation.edit.analysis import analyze_samples
from automation.edit.config import EditConfig
from automation.edit.cuts import apply_cut_list, build_silence_cuts
from automation.edit.mix import WaveSpec, mix_wav_files, read_wav


def _write_test_wav(path: Path, *, samples: array, spec: WaveSpec) -> None:
    """Write a WAV file for test fixtures."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav_handle:
        wav_handle.setnchannels(spec.channels)
        wav_handle.setsampwidth(spec.sample_width)
        wav_handle.setframerate(spec.sample_rate)
        wav_handle.writeframes(samples.tobytes())


def _build_samples(frames: list[int]) -> array:
    """Build a mono PCM sample buffer from frame values."""
    return array("h", frames)


def _write_24bit_wav(path: Path, *, frames: list[int], spec: WaveSpec) -> None:
    """Write a 24-bit PCM WAV file for format conversion tests."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = bytearray()
    for sample in frames:
        payload.extend(int(sample).to_bytes(3, byteorder="little", signed=True))
    with wave.open(str(path), "wb") as wav_handle:
        wav_handle.setnchannels(spec.channels)
        wav_handle.setsampwidth(3)
        wav_handle.setframerate(spec.sample_rate)
        wav_handle.writeframes(bytes(payload))


def test_analyze_samples_detects_silence() -> None:
    """merge overlapping speech: detect leading/trailing silence boundaries."""
    sample_rate = 10
    samples = _build_samples([0] * 5 + [12000] * 10 + [0] * 5)

    analysis = analyze_samples(
        samples,
        sample_rate=sample_rate,
        channels=1,
        sample_width=2,
        silence_threshold=0.1,
    )

    assert analysis.leading_silence_s == pytest.approx(0.5)
    assert analysis.trailing_silence_s == pytest.approx(0.5)


def test_apply_cut_list_trims_silence() -> None:
    """merge overlapping speech: trim silence segments based on config."""
    sample_rate = 10
    samples = _build_samples([0] * 5 + [12000] * 10 + [0] * 5)

    analysis = analyze_samples(
        samples,
        sample_rate=sample_rate,
        channels=1,
        sample_width=2,
        silence_threshold=0.1,
    )

    config = EditConfig(min_silence_duration_s=0.3, trim_padding_s=0.0)
    cuts = build_silence_cuts(analysis, config)
    trimmed = apply_cut_list(samples, sample_rate=sample_rate, channels=1, cuts=cuts)

    assert len(trimmed) == 10


def test_analyze_samples_all_silence() -> None:
    """merge overlapping speech: treat fully silent audio as all silence."""
    sample_rate = 10
    samples = _build_samples([0] * 10)

    analysis = analyze_samples(
        samples,
        sample_rate=sample_rate,
        channels=1,
        sample_width=2,
        silence_threshold=0.1,
    )

    assert analysis.leading_silence_s == pytest.approx(1.0)
    assert analysis.trailing_silence_s == pytest.approx(1.0)


def test_mix_wav_files(samples_dir: Path) -> None:
    """merge overlapping speech: ensure WAV mix keeps format and length."""
    spec = WaveSpec(sample_rate=8000, channels=1, sample_width=2)
    sample_a = _build_samples([1000] * 8)
    sample_b = _build_samples([2000] * 8)

    path_a = samples_dir / "a.wav"
    path_b = samples_dir / "b.wav"
    _write_test_wav(path_a, samples=sample_a, spec=spec)
    _write_test_wav(path_b, samples=sample_b, spec=spec)

    mixed, mixed_spec = mix_wav_files([path_a, path_b])

    assert mixed_spec == spec
    assert len(mixed) == 8


def test_mix_samples_handles_shorter_tracks(samples_dir: Path) -> None:
    """merge overlapping speech: avoid scaling down once tracks end."""
    spec = WaveSpec(sample_rate=8000, channels=1, sample_width=2)
    sample_a = _build_samples([1000] * 2)
    sample_b = _build_samples([2000] * 4)

    path_a = samples_dir / "short.wav"
    path_b = samples_dir / "long.wav"
    _write_test_wav(path_a, samples=sample_a, spec=spec)
    _write_test_wav(path_b, samples=sample_b, spec=spec)

    mixed, _ = mix_wav_files([path_a, path_b])

    assert list(mixed) == [1500, 1500, 2000, 2000]


def test_read_wav_converts_24bit(samples_dir: Path) -> None:
    """merge overlapping speech: down-convert 24-bit PCM to 16-bit samples."""
    spec = WaveSpec(sample_rate=8000, channels=1, sample_width=3)
    path = samples_dir / "twentyfour.wav"
    _write_24bit_wav(path, frames=[65536, -65536], spec=spec)

    samples, converted_spec = read_wav(path)

    assert converted_spec.sample_width == 2
    assert list(samples) == [256, -256]
