"""CLI entry point for the edit automation stage."""

from __future__ import annotations

import argparse
from array import array
from pathlib import Path
from typing import Sequence

from automation.edit.ai_guidance import generate_guidance
from automation.edit.analysis import analyze_samples
from automation.edit.config import build_edit_config, parse_extensions
from automation.edit.cuts import CutSegment, apply_cut_list, build_silence_cuts
from automation.edit.export import export_outputs
from automation.edit.meter import integrated_lufs, true_peak_dbfs
from automation.edit.mix import MixAlignment, WaveSpec, mix_wav_files, INTRO_DELAY_S
from automation.edit.transcript_sync import (
    apply_cuts_to_transcript,
    build_noise_cuts,
    find_phrase_timestamp,
    load_transcript_document,
)
from automation.transcript.config import build_transcription_config
from automation.transcript.generate import TranscriptionError, generate_transcript

HOST_INTRO_PHRASES = [
    "hi, this is maple history",
    "hi, and welcome back to maple history",
    "hi, and welcome to maple history",
]

NOISE_KEYWORDS = ["clap", "clapping", "laugh", "laughter"]


def _discover_audio_files(input_dir: Path, extensions: tuple[str, ...]) -> list[Path]:
    """Find audio files in a directory matching the allowed extensions."""
    candidates = [path for path in input_dir.iterdir() if path.is_file()]
    return sorted(
        [path for path in candidates if path.suffix.lower() in extensions],
        key=lambda path: path.name,
    )


def _load_transcript(transcript_path: Path | None):
    """Load a transcript document from disk if provided."""
    if transcript_path is None:
        return None
    if not transcript_path.exists():
        return None
    return load_transcript_document(transcript_path)


def _select_host_track(files: list[Path]) -> Path | None:
    for path in files:
        if "host" in path.name.lower():
            return path
    return files[0] if files else None


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser for edit automation."""
    parser = argparse.ArgumentParser(description=__doc__ or "edit.cli")
    parser.add_argument("--input", type=Path, required=True, help="Directory of WAV inputs")
    parser.add_argument("--output", type=Path, required=True, help="Output directory")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/edit.toml"),
        help="Optional TOML config file for edit settings",
    )
    parser.add_argument(
        "--silence-threshold",
        type=float,
        help="Normalized amplitude threshold for silence detection (0-1)",
    )
    parser.add_argument(
        "--min-silence",
        type=float,
        help="Minimum duration in seconds before trimming silence",
    )
    parser.add_argument(
        "--trim-padding",
        type=float,
        help="Seconds of padding to keep around trimmed silence",
    )
    parser.add_argument(
        "--extensions",
        help="Comma separated list of accepted audio extensions (default: .wav)",
    )
    parser.add_argument("--transcript", type=Path, help="Optional transcript text file")
    parser.add_argument(
        "--transcript-config",
        type=Path,
        default=Path("configs/transcript.toml"),
        help="Optional TOML config for automated transcription",
    )
    parser.add_argument("--dry-run", action="store_true", help="Only print planned actions")
    return parser


def _build_report(
    *,
    input_files: list[Path],
    spec: WaveSpec,
    analysis: dict,
    cuts: list[dict],
    guidance_count: int,
    transcript_updated: bool,
    loudness: dict,
    alignment: dict | None,
    transcript_source: str | None,
) -> dict:
    """Build the edit report payload for export."""
    return {
        "inputs": [str(path) for path in input_files],
        "wave_spec": {
            "sample_rate": spec.sample_rate,
            "channels": spec.channels,
            "sample_width": spec.sample_width,
        },
        "analysis": analysis,
        "cuts": cuts,
        "guidance_suggestions": guidance_count,
        "transcript_updated": transcript_updated,
        "loudness": loudness,
        "alignment": alignment or {},
        "transcript_source": transcript_source,
    }


def main(argv: Sequence[str] | None = None) -> int:
    """Run the edit automation pipeline."""
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    config = build_edit_config(
        config_path=args.config,
        silence_threshold=args.silence_threshold,
        min_silence_duration_s=args.min_silence,
        trim_padding_s=args.trim_padding,
        extensions=parse_extensions(args.extensions) if args.extensions else None,
    )

    if not args.input.exists():
        print(f"Input directory not found: {args.input}")
        return 1

    input_files = _discover_audio_files(args.input, config.normalized_extensions())
    if not input_files:
        print(f"No audio files found in {args.input}")
        return 1

    transcript_source_path: Path | None = args.transcript
    transcript_doc = _load_transcript(args.transcript)

    if args.dry_run:
        print("Edit stage dry run")
        print(f"Inputs ({len(input_files)}):")
        for path in input_files:
            print(f"  - {path}")
        print(f"Output directory: {args.output}")
        return 0

    host_phrase_s = None
    if transcript_doc:
        host_phrase_s = find_phrase_timestamp(transcript_doc, HOST_INTRO_PHRASES)
    else:
        host_track = _select_host_track(input_files)
        transcription_config = build_transcription_config(args.transcript_config, None)
        if host_track:
            try:
                generated_path = generate_transcript(host_track, args.output, transcription_config)
            except TranscriptionError as exc:
                print(f"Transcription failed: {exc}")
                generated_path = None
            if generated_path and generated_path.exists():
                transcript_source_path = generated_path
                transcript_doc = _load_transcript(generated_path)
                if transcript_doc:
                    host_phrase_s = find_phrase_timestamp(transcript_doc, HOST_INTRO_PHRASES)

    alignment = MixAlignment(host_trim_s=host_phrase_s)

    args.output.mkdir(parents=True, exist_ok=True)
    mix_result = mix_wav_files(input_files, alignment=alignment)
    mixed_samples = mix_result.mixed_samples
    spec = mix_result.spec

    analysis = analyze_samples(
        mixed_samples,
        sample_rate=spec.sample_rate,
        channels=spec.channels,
        sample_width=spec.sample_width,
        silence_threshold=config.silence_threshold,
    )

    cuts = build_silence_cuts(analysis, config)
    noise_cuts: list[CutSegment] = []
    if transcript_doc:
        noise_cuts = build_noise_cuts(
            transcript_doc,
            keywords=NOISE_KEYWORDS,
            host_trim_s=host_phrase_s or 0.0,
            intro_delay_s=INTRO_DELAY_S,
            padding_s=0.2,
        )
        cuts.extend(noise_cuts)
    trimmed_samples = apply_cut_list(
        mixed_samples,
        sample_rate=spec.sample_rate,
        channels=spec.channels,
        cuts=cuts,
    )

    trimmed_tracks: dict[str, array] = {}
    for track in mix_result.tracks:
        trimmed_track = apply_cut_list(
            track.samples,
            sample_rate=spec.sample_rate,
            channels=spec.channels,
            cuts=cuts,
        )
        if track.role in {"host", "guest"}:
            trimmed_tracks[track.role] = trimmed_track

    transcript_updated = False
    if transcript_doc is not None:
        result = apply_cuts_to_transcript(
            transcript_doc,
            cuts,
            host_trim_s=host_phrase_s or 0.0,
            intro_delay_s=INTRO_DELAY_S,
        )
        transcript_updated = result.updated_text != transcript_doc.text
        (args.output / "transcript.txt").write_text(result.updated_text, encoding="utf-8")

    guidance = generate_guidance(args.transcript)
    loudness = {
        "integrated_lufs": integrated_lufs(trimmed_samples),
        "true_peak_dbfs": true_peak_dbfs(trimmed_samples),
    }

    alignment_report = {
        "host_phrase_target_s": INTRO_DELAY_S,
        "host_phrase_detected_s": host_phrase_s,
        "noise_segments": len(noise_cuts),
    }

    report = _build_report(
        input_files=input_files,
        spec=spec,
        analysis={
            "duration_s": analysis.duration_s,
            "max_amplitude": analysis.max_amplitude,
            "leading_silence_s": analysis.leading_silence_s,
            "trailing_silence_s": analysis.trailing_silence_s,
        },
        cuts=[cut.__dict__ for cut in cuts],
        guidance_count=len(guidance),
        transcript_updated=transcript_updated,
        loudness=loudness,
        alignment=alignment_report,
        transcript_source=str(transcript_source_path) if transcript_source_path else None,
    )

    export_outputs(
        output_dir=args.output,
        samples=trimmed_samples,
        spec=spec,
        cuts=cuts,
        report=report,
        stems=trimmed_tracks,
    )

    print(f"Edit outputs written to {args.output}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
