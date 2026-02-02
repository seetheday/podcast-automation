"""Transcript stage automation and timestamp alignment."""

from .config import TranscriptionConfig, build_transcription_config
from .generate import generate_transcript, TranscriptionError

__all__ = [
    "TranscriptionConfig",
    "build_transcription_config",
    "generate_transcript",
    "TranscriptionError",
]
