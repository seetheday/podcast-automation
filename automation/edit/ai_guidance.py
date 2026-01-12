"""AI guidance placeholders for the edit stage."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GuidanceSuggestion:
    """A candidate edit suggestion produced by an AI pass."""

    start_s: float
    end_s: float
    label: str
    confidence: float
    notes: str


def generate_guidance(transcript_path: Path | None) -> list[GuidanceSuggestion]:
    """Return placeholder AI suggestions until MCP integrations are wired up."""
    # This keeps the pipeline deterministic while we still plan the AI integrations.
    if transcript_path is None or not transcript_path.exists():
        return []

    return [
        GuidanceSuggestion(
            start_s=0.0,
            end_s=0.0,
            label="no-op",
            confidence=0.0,
            notes="AI guidance integration pending; no changes suggested yet.",
        )
    ]
