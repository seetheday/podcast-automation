"""Export helpers for edit stage outputs."""

from __future__ import annotations

import json
import shutil
import subprocess
from array import array
from dataclasses import dataclass
from pathlib import Path

from automation.edit.cuts import CutSegment
from automation.edit.mix import WaveSpec, write_wav


@dataclass(frozen=True)
class ExportResult:
    """Summary of what the export step produced."""

    master_wav: Path
    delivery_mp3: Path | None
    report_path: Path
    cuts_path: Path


def write_cut_list(path: Path, cuts: list[CutSegment]) -> None:
    """Write the cut list to disk as JSON."""
    payload = [cut.__dict__ for cut in cuts]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))


def _ffmpeg_available() -> bool:
    """Return True if ffmpeg is available on PATH."""
    return shutil.which("ffmpeg") is not None


def encode_mp3(source_wav: Path, target_mp3: Path) -> bool:
    """Encode a WAV file to MP3 using ffmpeg when available."""
    if not _ffmpeg_available():
        return False

    target_mp3.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(source_wav),
            "-codec:a",
            "libmp3lame",
            "-q:a",
            "2",
            str(target_mp3),
        ],
        check=False,
        capture_output=True,
    )
    return target_mp3.exists()


def write_report(path: Path, report: dict) -> None:
    """Write an edit report to disk as JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2))


def export_outputs(
    *,
    output_dir: Path,
    samples: array,
    spec: WaveSpec,
    cuts: list[CutSegment],
    report: dict,
) -> ExportResult:
    """Write edit outputs to disk and return their locations."""
    master_wav = output_dir / "edited-master.wav"
    delivery_mp3 = output_dir / "edited-delivery.mp3"
    report_path = output_dir / "edit-report.json"
    cuts_path = output_dir / "cut-list.json"

    write_wav(master_wav, samples=samples, spec=spec)
    write_cut_list(cuts_path, cuts)
    write_report(report_path, report)

    mp3_created = encode_mp3(master_wav, delivery_mp3)
    return ExportResult(
        master_wav=master_wav,
        delivery_mp3=delivery_mp3 if mp3_created else None,
        report_path=report_path,
        cuts_path=cuts_path,
    )
