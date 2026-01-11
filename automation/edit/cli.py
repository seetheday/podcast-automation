"""CLI entry point for the edit automation stage."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from automation.edit.ai_guidance import generate_guidance
from automation.edit.analysis import analyze_samples
from automation.edit.config import build_edit_config, parse_extensions
from automation.edit.cuts import apply_cut_list, build_silence_cuts
from automation.edit.export import export_outputs
from automation.edit.mix import WaveSpec, mix_wav_files
from automation.edit.transcript_sync import apply_cuts_to_transcript


def _discover_audio_files(input_dir: Path, extensions: tuple[str, ...]) -> list[Path]:
    """Find audio files in a directory matching the allowed extensions."""
    candidates = [path for path in input_dir.iterdir() if path.is_file()]
    return sorted(
        [path for path in candidates if path.suffix.lower() in extensions],
        key=lambda path: path.name,
    )


def _load_transcript(transcript_path: Path | None) -> str | None:
    """Load a transcript from disk if provided."""
    if transcript_path is None:
        return None
    return transcript_path.read_text(encoding="utf-8")


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

    if args.dry_run:
        print("Edit stage dry run")
        print(f"Inputs ({len(input_files)}):")
        for path in input_files:
            print(f"  - {path}")
        print(f"Output directory: {args.output}")
        return 0

    args.output.mkdir(parents=True, exist_ok=True)
    mixed_samples, spec = mix_wav_files(input_files)

    analysis = analyze_samples(
        mixed_samples,
        sample_rate=spec.sample_rate,
        channels=spec.channels,
        sample_width=spec.sample_width,
        silence_threshold=config.silence_threshold,
    )

    cuts = build_silence_cuts(analysis, config)
    trimmed_samples = apply_cut_list(
        mixed_samples,
        sample_rate=spec.sample_rate,
        channels=spec.channels,
        cuts=cuts,
    )

    transcript_text = _load_transcript(args.transcript)
    transcript_updated = False
    if transcript_text is not None:
        result = apply_cuts_to_transcript(transcript_text, cuts)
        transcript_updated = result.updated_text != transcript_text
        (args.output / "transcript.txt").write_text(result.updated_text, encoding="utf-8")

    guidance = generate_guidance(args.transcript)
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
    )

    export_outputs(
        output_dir=args.output,
        samples=trimmed_samples,
        spec=spec,
        cuts=cuts,
        report=report,
    )

    print(f"Edit outputs written to {args.output}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
