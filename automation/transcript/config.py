"""Configuration helpers for automated transcription."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True)
class TranscriptionConfig:
    model_size: str = "small"
    temperature: float = 0.0
    word_replacements: Mapping[str, str] = field(default_factory=dict)


def load_transcription_settings(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    with path.open("rb") as handle:
        return tomllib.load(handle)


def build_transcription_config(
    config_path: Path | None,
    overrides: Mapping[str, str] | None,
) -> TranscriptionConfig:
    settings = load_transcription_settings(config_path)
    config = TranscriptionConfig()

    if "model_size" in settings:
        config = config.__class__(
            model_size=str(settings["model_size"]),
            temperature=config.temperature,
            word_replacements=settings.get("word_replacements", config.word_replacements),
        )
    if "temperature" in settings:
        config = config.__class__(
            model_size=config.model_size,
            temperature=float(settings["temperature"]),
            word_replacements=config.word_replacements,
        )
    replacements = settings.get("word_replacements")
    if isinstance(replacements, dict):
        config = config.__class__(
            model_size=config.model_size,
            temperature=config.temperature,
            word_replacements={k.lower(): str(v) for k, v in replacements.items()},
        )

    if overrides:
        merged = dict(config.word_replacements)
        merged.update({k.lower(): v for k, v in overrides.items()})
        config = config.__class__(
            model_size=config.model_size,
            temperature=config.temperature,
            word_replacements=merged,
        )

    return config
