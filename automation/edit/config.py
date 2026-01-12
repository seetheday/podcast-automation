"""Configuration helpers for the edit automation stage."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_AUDIO_EXTENSIONS = (".wav",)


@dataclass(frozen=True)
class EditConfig:
    """Configuration describing how the edit stage should behave."""

    silence_threshold: float = 0.02
    min_silence_duration_s: float = 0.5
    trim_padding_s: float = 0.1
    audio_extensions: tuple[str, ...] = DEFAULT_AUDIO_EXTENSIONS

    def normalized_extensions(self) -> tuple[str, ...]:
        """Normalize extension values to lowercase for comparisons."""
        return tuple(ext.lower() for ext in self.audio_extensions)


def load_config(path: Path | None) -> dict[str, Any]:
    """Load TOML config overrides if they exist."""
    if path is None or not path.exists():
        return {}
    with path.open("rb") as handle:
        return tomllib.load(handle)


def parse_extensions(raw: str | list[str] | None) -> tuple[str, ...] | None:
    """Parse extension values from CLI or config inputs."""
    if raw is None:
        return None
    if isinstance(raw, str):
        tokens = [token.strip() for token in raw.split(",") if token.strip()]
    else:
        tokens = [token.strip() for token in raw if token.strip()]
    if not tokens:
        raise ValueError("At least one audio extension must be provided")
    normalized = [token if token.startswith(".") else f".{token}" for token in tokens]
    return tuple(ext.lower() for ext in normalized)


def build_edit_config(
    *,
    config_path: Path | None,
    silence_threshold: float | None,
    min_silence_duration_s: float | None,
    trim_padding_s: float | None,
    extensions: tuple[str, ...] | None,
) -> EditConfig:
    """Build the edit configuration using file defaults and CLI overrides."""
    settings = load_config(config_path)
    config = EditConfig()

    if "silence_threshold" in settings:
        config = config.__class__(
            silence_threshold=float(settings["silence_threshold"]),
            min_silence_duration_s=config.min_silence_duration_s,
            trim_padding_s=config.trim_padding_s,
            audio_extensions=config.audio_extensions,
        )
    if "min_silence_duration_s" in settings:
        config = config.__class__(
            silence_threshold=config.silence_threshold,
            min_silence_duration_s=float(settings["min_silence_duration_s"]),
            trim_padding_s=config.trim_padding_s,
            audio_extensions=config.audio_extensions,
        )
    if "trim_padding_s" in settings:
        config = config.__class__(
            silence_threshold=config.silence_threshold,
            min_silence_duration_s=config.min_silence_duration_s,
            trim_padding_s=float(settings["trim_padding_s"]),
            audio_extensions=config.audio_extensions,
        )
    if "audio_extensions" in settings:
        parsed = parse_extensions(settings["audio_extensions"])
        if parsed:
            config = config.__class__(
                silence_threshold=config.silence_threshold,
                min_silence_duration_s=config.min_silence_duration_s,
                trim_padding_s=config.trim_padding_s,
                audio_extensions=parsed,
            )

    if silence_threshold is not None:
        config = config.__class__(
            silence_threshold=silence_threshold,
            min_silence_duration_s=config.min_silence_duration_s,
            trim_padding_s=config.trim_padding_s,
            audio_extensions=config.audio_extensions,
        )
    if min_silence_duration_s is not None:
        config = config.__class__(
            silence_threshold=config.silence_threshold,
            min_silence_duration_s=min_silence_duration_s,
            trim_padding_s=config.trim_padding_s,
            audio_extensions=config.audio_extensions,
        )
    if trim_padding_s is not None:
        config = config.__class__(
            silence_threshold=config.silence_threshold,
            min_silence_duration_s=config.min_silence_duration_s,
            trim_padding_s=trim_padding_s,
            audio_extensions=config.audio_extensions,
        )
    if extensions is not None:
        config = config.__class__(
            silence_threshold=config.silence_threshold,
            min_silence_duration_s=config.min_silence_duration_s,
            trim_padding_s=config.trim_padding_s,
            audio_extensions=extensions,
        )

    return config
