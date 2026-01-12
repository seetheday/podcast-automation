"""Tests for the edit stage pipeline helpers."""

from __future__ import annotations

import wave
from array import array
from pathlib import Path

import pytest

from automation.edit.analysis import analyze_samples
from automation.edit.config import EditConfig
from automation.edit.cuts import apply_cut_list, build_silence_cuts
from automation.edit.mix import WaveSpec, mix_wav_files


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


def _write_24bit_wav(path: Path, *, frames: list[int], sample_rate: int, channels: int) -> None:
    """Write a simple 24-bit WAV file from a list of mono frame values."""
    path.parent.mkdir(parents=True, exist_ok=True)
    packed = bytearray()
    for value in frames:
        packed.extend(int(value).to_bytes(3, byteorder="little", signed=True))
    with wave.open(str(path), "wb") as wav_handle:
        wav_handle.setnchannels(channels)
        wav_handle.setsampwidth(3)
        wav_handle.setframerate(sample_rate)
        wav_handle.writeframes(packed)


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


def test_mix_wav_files_downsamples_24_bit(samples_dir: Path) -> None:
    """merge overlapping speech: allow 24-bit WAVs to mix with 16-bit tracks."""
    sample_rate = 44100
    channels = 1
    host_24 = samples_dir / "host24.wav"
    guest_24 = samples_dir / "guest24.wav"
    intro_16 = samples_dir / "intro16.wav"

    _write_24bit_wav(host_24, frames=[1000] * 4, sample_rate=sample_rate, channels=channels)
    _write_24bit_wav(guest_24, frames=[500] * 4, sample_rate=sample_rate, channels=channels)

    spec_16 = WaveSpec(sample_rate=sample_rate, channels=channels, sample_width=2)
    _write_test_wav(intro_16, samples=_build_samples([250] * 4), spec=spec_16)

    mixed, mixed_spec = mix_wav_files([host_24, guest_24, intro_16])

    assert mixed_spec.sample_width == 2
    assert mixed_spec.sample_rate == sample_rate
    assert len(mixed) == 4
