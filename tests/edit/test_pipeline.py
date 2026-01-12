"""Tests for the edit stage pipeline helpers."""

from __future__ import annotations

import wave
from array import array
from pathlib import Path

import pytest

from automation.edit.analysis import analyze_samples
from automation.edit.config import EditConfig
from automation.edit.cuts import apply_cut_list, build_silence_cuts
from automation.edit.mix import MixAlignment, WaveSpec, mix_wav_files, seconds_to_samples


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

    result = mix_wav_files([path_a, path_b])

    assert result.spec == spec
    assert len(result.mixed_samples) == 8


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

    result = mix_wav_files([host_24, guest_24, intro_16])

    assert result.spec.sample_width == 2
    assert result.spec.sample_rate == sample_rate


def test_host_track_is_offset_by_intro_delay(samples_dir: Path) -> None:
    """intro-to-host timing: host audio starts after configured intro delay."""
    spec = WaveSpec(sample_rate=10, channels=1, sample_width=2)
    host_samples = _build_samples([1000, 1100, 1200])
    host_path = samples_dir / "Sample-Host-Raw.wav"
    _write_test_wav(host_path, samples=host_samples, spec=spec)

    result = mix_wav_files([host_path])

    offset = seconds_to_samples(6.836, result.spec.sample_rate, result.spec.channels)
    assert all(value == 0 for value in result.mixed_samples[:offset])
    assert result.mixed_samples[offset] == host_samples[0]


def test_intro_music_fade_envelope(samples_dir: Path) -> None:
    """intro-to-host timing: intro music follows the defined fade envelope."""
    spec = WaveSpec(sample_rate=10, channels=1, sample_width=2)
    duration_samples = seconds_to_samples(13, spec.sample_rate, spec.channels)
    samples = _build_samples([1000] * (duration_samples + 10))
    music_path = samples_dir / "Sample-Intro-Outro-Music.wav"
    _write_test_wav(music_path, samples=samples, spec=spec)

    result = mix_wav_files([music_path])
    mixed = result.mixed_samples

    initial_gain = 10 ** (-1.0 / 20.0)
    assert mixed[0] == pytest.approx(int(round(1000 * initial_gain)))

    post_fade_index = seconds_to_samples(12.6, spec.sample_rate, spec.channels)
    assert all(value == 0 for value in mixed[post_fade_index:post_fade_index + 5])


def test_mix_alignment_trims_host_leading_audio(samples_dir: Path) -> None:
    spec = WaveSpec(sample_rate=10, channels=1, sample_width=2)
    host_samples = _build_samples([0, 0, 1000, 1100])
    host_path = samples_dir / "Host.wav"
    _write_test_wav(host_path, samples=host_samples, spec=spec)

    result = mix_wav_files([host_path], alignment=MixAlignment(host_trim_s=0.2))

    offset = seconds_to_samples(6.836, spec.sample_rate, spec.channels)
    assert result.mixed_samples[offset] == 1000


def test_guest_track_stays_in_sync_with_host_trim(samples_dir: Path) -> None:
    spec = WaveSpec(sample_rate=10, channels=1, sample_width=2)
    host_samples = _build_samples([0, 0, 1000, 1100])
    guest_samples = _build_samples([0, 0, 2000, 2100])
    host_path = samples_dir / "Sample-Host-Raw.wav"
    guest_path = samples_dir / "Sample-Guest-Raw.wav"
    _write_test_wav(host_path, samples=host_samples, spec=spec)
    _write_test_wav(guest_path, samples=guest_samples, spec=spec)

    result = mix_wav_files([host_path, guest_path], alignment=MixAlignment(host_trim_s=0.2))

    offset = seconds_to_samples(6.836, spec.sample_rate, spec.channels)
    host_track = next(track for track in result.tracks if track.role == "host")
    guest_track = next(track for track in result.tracks if track.role == "guest")
    assert host_track.samples[offset] == 1000
    assert guest_track.samples[offset] == 2000
