"""Build and apply cut lists for edit automation."""

from __future__ import annotations

from array import array
from dataclasses import dataclass

from automation.edit.analysis import AudioAnalysis
from automation.edit.config import EditConfig


@dataclass(frozen=True)
class CutSegment:
    """A region to remove from the audio timeline."""

    start_s: float
    end_s: float
    reason: str


@dataclass(frozen=True)
class KeepSegment:
    """A region to keep from the audio timeline."""

    start_s: float
    end_s: float


def build_silence_cuts(analysis: AudioAnalysis, config: EditConfig) -> list[CutSegment]:
    """Build a list of cuts for leading and trailing silence."""
    cuts: list[CutSegment] = []

    if analysis.leading_silence_s >= config.min_silence_duration_s:
        end_s = max(analysis.leading_silence_s - config.trim_padding_s, 0.0)
        cuts.append(CutSegment(start_s=0.0, end_s=end_s, reason="leading_silence"))

    if analysis.trailing_silence_s >= config.min_silence_duration_s:
        start_s = max(
            analysis.duration_s - analysis.trailing_silence_s + config.trim_padding_s, 0.0
        )
        cuts.append(
            CutSegment(start_s=start_s, end_s=analysis.duration_s, reason="trailing_silence")
        )

    return cuts


def compute_keep_segments(duration_s: float, cuts: list[CutSegment]) -> list[KeepSegment]:
    """Compute the list of segments that remain after applying cuts."""
    if not cuts:
        return [KeepSegment(start_s=0.0, end_s=duration_s)]

    normalized = sorted(cuts, key=lambda cut: cut.start_s)
    keep_segments: list[KeepSegment] = []
    current_start = 0.0

    for cut in normalized:
        if cut.start_s > current_start:
            keep_segments.append(KeepSegment(start_s=current_start, end_s=cut.start_s))
        current_start = max(current_start, cut.end_s)

    if current_start < duration_s:
        keep_segments.append(KeepSegment(start_s=current_start, end_s=duration_s))

    return keep_segments


def apply_cut_list(
    samples: array,
    *,
    sample_rate: int,
    channels: int,
    cuts: list[CutSegment],
) -> array:
    """Apply cuts to a sample buffer and return the trimmed result."""
    if not cuts:
        return samples

    total_frames = len(samples) // channels
    duration_s = total_frames / sample_rate if sample_rate else 0.0
    keep_segments = compute_keep_segments(duration_s, cuts)
    trimmed = array("h")

    for segment in keep_segments:
        start_frame = int(segment.start_s * sample_rate)
        end_frame = int(segment.end_s * sample_rate)
        # Copy the PCM frames for each kept region into the output buffer.
        start_index = start_frame * channels
        end_index = end_frame * channels
        trimmed.extend(samples[start_index:end_index])

    return trimmed
