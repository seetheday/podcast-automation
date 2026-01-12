"""Transcript alignment utilities for the edit automation stage."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from automation.edit.cuts import CutSegment


@dataclass(frozen=True)
class TranscriptSegment:
    """A timestamped snippet extracted from a transcript."""

    start_s: float
    end_s: float
    text: str


@dataclass(frozen=True)
class TranscriptDocument:
    """Structured transcript consisting of segments and the raw text."""

    text: str
    segments: tuple[TranscriptSegment, ...]


@dataclass(frozen=True)
class TranscriptSyncResult:
    """Result metadata for transcript synchronization."""

    updated_text: str
    removed_segments: int


def load_transcript_document(path: Path) -> TranscriptDocument:
    """Load a transcript document from JSON (preferred) or plain text."""

    raw = path.read_text(encoding="utf-8")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return TranscriptDocument(text=raw, segments=())

    segments: list[TranscriptSegment] = []
    for segment in payload.get("segments", []):
        try:
            start_s = float(segment["start"])
            end_s = float(segment["end"])
            text = str(segment.get("text", ""))
        except (KeyError, TypeError, ValueError):
            continue
        segments.append(TranscriptSegment(start_s=start_s, end_s=end_s, text=text))

    text_value = payload.get("text")
    if text_value is None and segments:
        text_value = "\n".join(segment.text for segment in segments)
    if text_value is None:
        text_value = raw

    return TranscriptDocument(text=text_value, segments=tuple(segments))


def apply_cuts_to_transcript(
    document: TranscriptDocument,
    cuts: list[CutSegment],
    *,
    host_trim_s: float,
    intro_delay_s: float,
) -> TranscriptSyncResult:
    """Remove transcript segments that overlap any applied cut."""

    if not document.segments or not cuts:
        return TranscriptSyncResult(updated_text=document.text, removed_segments=0)

    normalized_cuts = sorted(cuts, key=lambda cut: cut.start_s)
    kept_text: list[str] = []
    removed = 0

    for segment in document.segments:
        start_s = _realign_timestamp(segment.start_s, host_trim_s, intro_delay_s)
        end_s = _realign_timestamp(segment.end_s, host_trim_s, intro_delay_s)
        if _segment_overlaps_cut(start_s, end_s, normalized_cuts):
            removed += 1
            continue
        kept_text.append(segment.text.strip())

    updated_text = "\n".join(filter(None, kept_text)) or document.text
    return TranscriptSyncResult(updated_text=updated_text, removed_segments=removed)


def find_phrase_timestamp(document: TranscriptDocument, phrases: Iterable[str]) -> float | None:
    """Locate the timestamp for the first transcript segment containing one of the phrases."""

    if not document.segments:
        return None

    normalized_phrases = [normalize_text(phrase) for phrase in phrases]
    for segment in document.segments:
        segment_text = normalize_text(segment.text)
        if any(phrase in segment_text for phrase in normalized_phrases):
            return segment.start_s
    return None


def build_noise_cuts(
    document: TranscriptDocument,
    *,
    keywords: Iterable[str],
    host_trim_s: float,
    intro_delay_s: float,
    padding_s: float = 0.1,
) -> list[CutSegment]:
    """Build targeted cuts for transcript segments containing the supplied keywords."""

    cuts: list[CutSegment] = []
    normalized_keywords = [normalize_text(keyword) for keyword in keywords]

    for segment in document.segments:
        normalized_text = normalize_text(segment.text)
        if not any(keyword in normalized_text for keyword in normalized_keywords):
            continue

        # Align segment timestamps to the final mix timeline once the host track is trimmed
        start_s = segment.start_s - host_trim_s
        end_s = segment.end_s - host_trim_s
        if end_s <= 0:
            continue  # removed during host trim

        start_s = max(start_s, 0.0) + intro_delay_s - padding_s
        end_s = max(end_s, 0.0) + intro_delay_s + padding_s
        cuts.append(CutSegment(start_s=start_s, end_s=end_s, reason="transcript_noise"))

    return cuts


def normalize_text(value: str) -> str:
    """Normalize transcript text for fuzzy matching."""
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _realign_timestamp(original_s: float, host_trim_s: float, intro_delay_s: float) -> float:
    adjusted = max(original_s - host_trim_s, 0.0)
    return adjusted + intro_delay_s


def _segment_overlaps_cut(start_s: float, end_s: float, cuts: list[CutSegment]) -> bool:
    if end_s <= start_s:
        return False
    for cut in cuts:
        if cut.end_s <= start_s:
            continue
        if cut.start_s >= end_s:
            break
        if cut.start_s < end_s and cut.end_s > start_s:
            return True
    return False
