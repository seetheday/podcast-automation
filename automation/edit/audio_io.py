"""Shared audio I/O helpers for the edit stage."""

from __future__ import annotations

from array import array


def convert_24bit_to_16bit(frames: bytes) -> array:
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


def read_pcm_samples(frames: bytes, *, sample_width: int) -> tuple[array, int]:
    """Read PCM frames into 16-bit samples, normalizing when needed."""
    if sample_width == 2:
        samples = array("h")
        samples.frombytes(frames)
        return samples, sample_width

    if sample_width == 3:
        samples = convert_24bit_to_16bit(frames)
        return samples, 2

    raise ValueError("Only 16-bit and 24-bit PCM WAV files are supported")
