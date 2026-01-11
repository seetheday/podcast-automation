"""Audio mixing utilities for edit automation."""

from __future__ import annotations

import wave
from array import array
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WaveSpec:
    """Wave format parameters used to validate compatibility between tracks."""

    sample_rate: int
    channels: int
    sample_width: int


def _convert_24bit_to_16bit(frames: bytes) -> array:
    """Convert 24-bit PCM frames into 16-bit PCM samples."""
    samples = array("h")
    for index in range(0, len(frames), 3):
        chunk = frames[index : index + 3]
        if len(chunk) < 3:
            continue
        sample_24 = int.from_bytes(chunk, byteorder="little", signed=True)
        sample_16 = max(min(sample_24 >> 8, 32767), -32768)
        samples.append(sample_16)
    return samples


def read_wav(path: Path) -> tuple[array, WaveSpec]:
    """Read a WAV file into an array of samples and return its format spec."""
    with wave.open(str(path), "rb") as wav_handle:
        spec = WaveSpec(
            sample_rate=wav_handle.getframerate(),
            channels=wav_handle.getnchannels(),
            sample_width=wav_handle.getsampwidth(),
        )
        frames = wav_handle.readframes(wav_handle.getnframes())

    if spec.sample_width == 2:
        samples = array("h")
        samples.frombytes(frames)
        return samples, spec

    if spec.sample_width == 3:
        samples = _convert_24bit_to_16bit(frames)
        converted_spec = WaveSpec(
            sample_rate=spec.sample_rate,
            channels=spec.channels,
            sample_width=2,
        )
        return samples, converted_spec

    raise ValueError("Only 16-bit and 24-bit PCM WAV files are supported for mixing")


def ensure_matching_specs(specs: list[WaveSpec]) -> WaveSpec:
    """Ensure all WAV specs match so the mix stays aligned."""
    if not specs:
        raise ValueError("At least one WAV spec is required for mixing")

    first = specs[0]
    for spec in specs[1:]:
        if spec != first:
            raise ValueError("All WAV files must share the same format for mixing")
    return first


def mix_samples(tracks: list[array]) -> array:
    """Mix multiple PCM tracks by averaging samples across tracks."""
    if not tracks:
        raise ValueError("At least one track is required for mixing")

    max_length = max(len(track) for track in tracks)
    mixed = array("h", [0] * max_length)

    for index in range(max_length):
        # For each PCM index, sum samples across tracks and average them.
        summed = 0
        for track in tracks:
            if index < len(track):
                summed += track[index]
        averaged = int(summed / len(tracks))
        mixed[index] = max(min(averaged, 32767), -32768)

    return mixed


def mix_wav_files(paths: list[Path]) -> tuple[array, WaveSpec]:
    """Read and mix WAV files, returning the combined sample buffer and spec."""
    tracks: list[array] = []
    specs: list[WaveSpec] = []

    for path in paths:
        samples, spec = read_wav(path)
        tracks.append(samples)
        specs.append(spec)

    spec = ensure_matching_specs(specs)
    mixed = mix_samples(tracks)
    return mixed, spec


def write_wav(path: Path, *, samples: array, spec: WaveSpec) -> None:
    """Write a sample buffer back to a WAV file on disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav_handle:
        wav_handle.setnchannels(spec.channels)
        wav_handle.setsampwidth(spec.sample_width)
        wav_handle.setframerate(spec.sample_rate)
        wav_handle.writeframes(samples.tobytes())
