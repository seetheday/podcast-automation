"""Audio mixing utilities for edit automation."""

from __future__ import annotations

import wave
from array import array
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from automation.edit.audio_io import read_pcm_samples


@dataclass(frozen=True)
class MixAlignment:
    """Optional directives for positioning tracks before mixing."""

    host_trim_s: float | None = None

INTRO_DELAY_S = 6.836
# (time_seconds, dBFS) pairs describing the intro music fade.
INTRO_MUSIC_FADE = (
    (0.0, -1.0),
    (6.836, -1.0),
    (6.962, -5.5),
    (7.9, -9.5),
    (9.4, -12.5),
    (10.7, -19.4),
    (11.5, -26.3),
    (12.341, -120.0),
)


@dataclass(frozen=True)
class WaveSpec:
    """Wave format parameters used to validate compatibility between tracks."""

    sample_rate: int
    channels: int
    sample_width: int


@dataclass(frozen=True)
class GainPoint:
    """Gain control point describing dBFS at a specific second."""

    time_s: float
    gain_linear: float


@dataclass(frozen=True)
class TrackPlacement:
    """Placement and envelope metadata for a single input track."""

    path: Path
    role: str
    offset_samples: int
    trim_leading_samples: int = 0
    envelope: tuple[GainPoint, ...] | None = None

    def gain_for_sample(self, sample_index: int, *, sample_rate: int, channels: int) -> float:
        if not self.envelope:
            return 1.0
        frame_index = sample_index // channels
        time_s = frame_index / sample_rate
        return interpolate_gain(self.envelope, time_s)


@dataclass(frozen=True)
class AlignedTrack:
    """Track samples aligned to the shared mix timeline."""

    path: Path
    role: str
    samples: array


@dataclass(frozen=True)
class MixResult:
    """Full context from the mixing stage."""

    mixed_samples: array
    spec: WaveSpec
    tracks: tuple[AlignedTrack, ...]


def read_wav(path: Path) -> tuple[array, WaveSpec]:
    """Read a WAV file into an array of samples and return its format spec."""
    with wave.open(str(path), "rb") as wav_handle:
        sample_rate = wav_handle.getframerate()
        channels = wav_handle.getnchannels()
        sample_width = wav_handle.getsampwidth()
        frames = wav_handle.readframes(wav_handle.getnframes())

    samples, normalized_width = read_pcm_samples(frames, sample_width=sample_width)
    spec = WaveSpec(sample_rate=sample_rate, channels=channels, sample_width=normalized_width)
    return samples, spec


def ensure_matching_specs(specs: list[WaveSpec]) -> WaveSpec:
    """Ensure all WAV specs match so the mix stays aligned."""
    if not specs:
        raise ValueError("At least one WAV spec is required for mixing")

    first = specs[0]
    for spec in specs[1:]:
        if spec != first:
            raise ValueError("All WAV files must share the same format for mixing")
    return first


def _align_tracks(
    tracks: Sequence[array],
    placements: Sequence[TrackPlacement],
    *,
    sample_rate: int,
    channels: int,
) -> tuple[list[AlignedTrack], array]:
    if not tracks:
        raise ValueError("At least one track is required for mixing")

    total_length = 0
    effective_lengths: list[int] = []
    for track, placement in zip(tracks, placements):
        effective = max(len(track) - placement.trim_leading_samples, 0)
        effective_lengths.append(effective)
        candidate = placement.offset_samples + effective
        total_length = max(total_length, candidate)

    accumulator = [0.0] * total_length
    aligned: list[AlignedTrack] = []

    for track, placement, effective in zip(tracks, placements, effective_lengths):
        aligned_samples = array("h", [0] * total_length)
        trim = min(placement.trim_leading_samples, len(track))
        for rel_index in range(effective):
            src_index = trim + rel_index
            dest = placement.offset_samples + rel_index
            if dest >= total_length:
                break
            gain = placement.gain_for_sample(rel_index, sample_rate=sample_rate, channels=channels)
            processed = max(min(int(round(track[src_index] * gain)), 32767), -32768)
            aligned_samples[dest] = processed
            accumulator[dest] += processed
        aligned.append(AlignedTrack(path=placement.path, role=placement.role, samples=aligned_samples))

    mixed = array("h", [0] * total_length)
    for index, value in enumerate(accumulator):
        mixed[index] = max(min(int(round(value)), 32767), -32768)

    return aligned, mixed


def mix_wav_files(paths: list[Path], alignment: MixAlignment | None = None) -> MixResult:
    """Read and mix WAV files, returning the combined sample buffer and aligned tracks."""
    tracks: list[array] = []
    specs: list[WaveSpec] = []

    for path in paths:
        samples, spec = read_wav(path)
        tracks.append(samples)
        specs.append(spec)

    spec = ensure_matching_specs(specs)
    placements = build_track_placements(paths, spec, alignment)
    aligned_tracks, mixed = _align_tracks(
        tracks, placements, sample_rate=spec.sample_rate, channels=spec.channels
    )
    return MixResult(mixed_samples=mixed, spec=spec, tracks=tuple(aligned_tracks))


def write_wav(path: Path, *, samples: array, spec: WaveSpec) -> None:
    """Write a sample buffer back to a WAV file on disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav_handle:
        wav_handle.setnchannels(spec.channels)
        wav_handle.setsampwidth(spec.sample_width)
        wav_handle.setframerate(spec.sample_rate)
        wav_handle.writeframes(samples.tobytes())


def build_track_placements(
    paths: Iterable[Path], spec: WaveSpec, alignment: MixAlignment | None
) -> list[TrackPlacement]:
    """Create placement metadata for each track based on naming conventions."""
    placements: list[TrackPlacement] = []
    host_trim_samples = 0
    if alignment and alignment.host_trim_s and alignment.host_trim_s > 0:
        host_trim_samples = seconds_to_samples(alignment.host_trim_s, spec.sample_rate, spec.channels)
    for path in paths:
        role = classify_track(path)
        offset = 0
        trim = 0
        envelope: tuple[GainPoint, ...] | None = None
        if role in {"host", "guest"}:
            offset = seconds_to_samples(INTRO_DELAY_S, spec.sample_rate, spec.channels)
        if role in {"host", "guest"} and host_trim_samples:
            trim = host_trim_samples
        if role == "music":
            envelope = build_music_envelope()
        placements.append(
            TrackPlacement(
                path=path,
                role=role,
                offset_samples=offset,
                trim_leading_samples=trim,
                envelope=envelope,
            )
        )
    return placements


def classify_track(path: Path) -> str:
    """Infer the role of a track from its filename."""
    name = path.name.lower()
    if "intro" in name or "music" in name:
        return "music"
    if "host" in name:
        return "host"
    if "guest" in name:
        return "guest"
    return "dialog"


def seconds_to_samples(seconds: float, sample_rate: int, channels: int) -> int:
    """Convert seconds to sample-count including channel interleaves."""
    frames = int(round(seconds * sample_rate))
    return frames * channels


def build_music_envelope() -> tuple[GainPoint, ...]:
    """Construct the intro music gain envelope points."""
    return tuple(GainPoint(time_s=point[0], gain_linear=db_to_gain(point[1])) for point in INTRO_MUSIC_FADE)


def db_to_gain(value_db: float) -> float:
    if value_db <= -120.0:
        return 0.0
    return 10 ** (value_db / 20.0)


def interpolate_gain(points: Sequence[GainPoint], time_s: float) -> float:
    if not points:
        return 1.0
    if time_s <= points[0].time_s:
        return points[0].gain_linear
    for left, right in zip(points, points[1:]):
        if time_s <= right.time_s:
            span = right.time_s - left.time_s
            if span <= 0:
                return right.gain_linear
            ratio = (time_s - left.time_s) / span
            return left.gain_linear + ratio * (right.gain_linear - left.gain_linear)
    return points[-1].gain_linear
