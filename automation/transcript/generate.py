"""Transcription utilities built on top of OpenAI Whisper."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from automation.transcript.config import TranscriptionConfig

try:
    import whisper  # type: ignore
except Exception:  # pragma: no cover
    whisper = None


@dataclass
class TranscriptionResult:
    text: str
    segments: list[dict]
    output_path: Path


class TranscriptionError(RuntimeError):
    """Raised when the transcription step cannot complete."""


def generate_transcript(
    audio_path: Path,
    output_dir: Path,
    config: TranscriptionConfig,
) -> Path:
    """Transcribe the provided audio file and write a Whisper-style JSON output."""

    if whisper is None:  # pragma: no cover - depends on environment
        raise TranscriptionError(
            "openai-whisper is not installed. Run `pip install openai-whisper` to enable auto transcription."
        )

    if not audio_path.exists():
        raise TranscriptionError(f"Audio file not found: {audio_path}")

    model = whisper.load_model(config.model_size)
    result = model.transcribe(str(audio_path), temperature=config.temperature)

    segments = [dict(segment) for segment in result.get("segments", [])]
    apply_word_replacements(segments, config.word_replacements)

    text = result.get("text", "")
    if text:
        text = replace_words(text, config.word_replacements)

    payload = {
        "text": text,
        "segments": segments,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    target_path = output_dir / f"{audio_path.stem}-transcript.json"
    target_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return target_path


def apply_word_replacements(segments: list[dict], replacements: Mapping[str, str]) -> None:
    if not replacements:
        return
    normalized = {key.lower(): value for key, value in replacements.items()}
    for segment in segments:
        text = segment.get("text")
        if not isinstance(text, str):
            continue
        segment["text"] = replace_words(text, normalized)


_WORD_PATTERN = re.compile(r"[A-Za-z']+")


def replace_words(text: str, replacements: Mapping[str, str]) -> str:
    if not replacements:
        return text

    lower_map = {key.lower(): value for key, value in replacements.items()}

    def _replace(match: re.Match[str]) -> str:
        original = match.group(0)
        replacement = lower_map.get(original.lower())
        if not replacement:
            return original
        if original.isupper():
            return replacement.upper()
        if original[0].isupper():
            return replacement.capitalize()
        return replacement

    return _WORD_PATTERN.sub(_replace, text)
