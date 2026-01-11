"""Transcript alignment utilities for the edit automation stage."""

from __future__ import annotations

from dataclasses import dataclass

from automation.edit.cuts import CutSegment


@dataclass(frozen=True)
class TranscriptSyncResult:
    """Result metadata for transcript synchronization."""

    updated_text: str
    removed_segments: int


def apply_cuts_to_transcript(transcript_text: str, cuts: list[CutSegment]) -> TranscriptSyncResult:
    """Return transcript text unchanged until alignment tooling is available."""
    # Keep deterministic behavior by recording how many cuts were requested
    # even though we are not yet slicing timestamps out of the transcript.
    return TranscriptSyncResult(updated_text=transcript_text, removed_segments=len(cuts))
