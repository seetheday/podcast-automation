"""Audio analysis helpers for the edit automation stage."""

from __future__ import annotations

import wave
from array import array
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AudioAnalysis:
    """Summary metrics derived from a WAV file or sample buffer."""

    duration_s: float
    sample_rate: int
    channels: int
    sample_width: int
    max_amplitude: float
    leading_silence_s: float
    trailing_silence_s: float


def _to_float(sample: int, max_value: float) -> float:
    """Convert a PCM sample into a normalized float value."""
    return abs(sample) / max_value


def analyze_samples(
    samples: array,
    *,
    sample_rate: int,
    channels: int,
    sample_width: int,
    silence_threshold: float,
) -> AudioAnalysis:
    """Analyze sample buffers for duration and silence characteristics."""
    if sample_width != 2:
        raise ValueError("Only 16-bit PCM WAV files are supported for analysis")
    if channels <= 0:
        raise ValueError("Audio must contain at least one channel")

    total_frames = len(samples) // channels
    duration_s = total_frames / sample_rate if sample_rate else 0.0
    max_value = float(2 ** (sample_width * 8 - 1))

    # Walk samples to find maximum amplitude and locate leading/trailing silence.
    max_amplitude = 0.0
    leading_frame = 0
    trailing_frame = total_frames

    for frame_index in range(total_frames):
        frame_start = frame_index * channels
        frame_slice = samples[frame_start : frame_start + channels]
        frame_max = max(_to_float(sample, max_value) for sample in frame_slice)
        max_amplitude = max(max_amplitude, frame_max)
        if frame_max >= silence_threshold:
            leading_frame = frame_index
            break

    for frame_index in range(total_frames - 1, -1, -1):
        frame_start = frame_index * channels
        frame_slice = samples[frame_start : frame_start + channels]
        frame_max = max(_to_float(sample, max_value) for sample in frame_slice)
        if frame_max >= silence_threshold:
            trailing_frame = frame_index
            break

    leading_silence_s = leading_frame / sample_rate if sample_rate else 0.0
    trailing_silence_s = (total_frames - trailing_frame - 1) / sample_rate if sample_rate else 0.0

    return AudioAnalysis(
        duration_s=duration_s,
        sample_rate=sample_rate,
        channels=channels,
        sample_width=sample_width,
        max_amplitude=max_amplitude,
        leading_silence_s=leading_silence_s,
        trailing_silence_s=trailing_silence_s,
    )


def analyze_wav_file(path: Path, *, silence_threshold: float) -> AudioAnalysis:
    """Analyze a WAV file on disk and return summary metrics."""
    with wave.open(str(path), "rb") as wav_handle:
        sample_rate = wav_handle.getframerate()
        channels = wav_handle.getnchannels()
        sample_width = wav_handle.getsampwidth()
        frames = wav_handle.readframes(wav_handle.getnframes())

    if sample_width == 2:
        samples = array("h")
        samples.frombytes(frames)
    elif sample_width == 3:
        samples = array("h")
        for index in range(0, len(frames), 3):
            chunk = frames[index : index + 3]
            if len(chunk) < 3:
                continue
            sample_24 = int.from_bytes(chunk, byteorder="little", signed=True)
            samples.append(max(min(sample_24 >> 8, 32767), -32768))
        sample_width = 2
    else:
        raise ValueError("Only 16-bit and 24-bit PCM WAV files are supported for analysis")

    return analyze_samples(
        samples,
        sample_rate=sample_rate,
        channels=channels,
        sample_width=sample_width,
        silence_threshold=silence_threshold,
    )
