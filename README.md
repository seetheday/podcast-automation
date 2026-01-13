# Podcast Automation

Tools and agents for turning the Maple History podcast workflow into a reproducible automation pipeline. The repo mirrors the original manual process (record → edit → publish) while providing deterministic CLIs, sample assets, and tests so each stage can be evolved independently.

## Repository Layout
- `automation/` – stage-specific Python packages (`ingest`, `edit`, `transcript`, etc.) with CLI entry points.
- `assets/audio/samples/` – small WAV fixtures (host, guest, intro) used for local testing.
- `configs/` – TOML defaults (`ingest.example.toml`, `edit.toml`, `transcript.example.toml`) to copy/override per machine.
- `tests/` – pytest suites mirroring each stage (`tests/ingest`, `tests/edit`, `tests/transcript`).
- `outputs/` – working directory for CLI results (mixed WAV/MP3, stems, cut lists, reports, generated transcripts).
- `Original-manual-workflow.md`, `plan.md`, `TODO.md`, `handoff.md` – documentation of the legacy workflow, current plan, backlog, and latest status.

## Getting Started
1. **Python environment** – Python 3.11+, create a venv: `python -m venv .venv && source .venv/bin/activate`.
2. **System deps** – Install `ffmpeg` (MP3 rendering) and GPU-friendly `torch` if running Whisper locally. Whisper needs build tools + `rust` for faster installs.
3. **Install requirements** – `pip install -r requirements.txt` (installs `ruff`, `pytest`, `openai-whisper`).
4. **Optional configs** – copy `configs/ingest.example.toml` to `configs/ingest.toml`, same for `transcript` and (when created) `edit`, then customize paths, intro-delay overrides, or transcript spelling rules.

## Key Workflows
### Ingest
Catalog synced Reaper sessions and existing renders.
```bash
python -m automation.ingest.sync \
  --config configs/ingest.toml \
  --episode "Huron Carol"
```
Outputs a summary of `<episode>/Media/*.wav`, render status in `final audio/`, and highlights missing/duplicate MP3s.

### Edit
Mix host/guest/intro tracks, enforce the intro envelope, auto-transcribe the host track (if no transcript file is provided), trim clap/laugh segments, and export stems.
```bash
python -m automation.edit.cli \
  --input assets/audio/samples \
  --output outputs/edit-sample
```
Results:
- `edited-master.wav` + MP3 for quick review.
- `edited-master-host.wav` / `edited-master-guest.wav` so you can keep editing tracks independently in Reaper.
- `cut-list.json`, `edit-report.json` (wave spec, loudness, alignment metadata, transcript source), and a trimmed `transcript.txt` that matches the cuts.
- Pass `--transcript path/to/whisper.json` to reuse an existing transcript; otherwise the CLI runs Whisper using `configs/transcript.toml` and applies the configured word replacements.

## Configuration Highlights
- **Ingest** – `source_root`, `render_dir`, and allowed extensions; detect missing renders.
- **Edit** – Silence thresholds, padding, intro targets; transcript auto-detected phrases (`HOST_INTRO_PHRASES`) ensure “Hi…” lands at 6.836 s.
- **Transcript** – Whisper model, temperature, and `word_replacements` dictionary so names like “Christina” always use the preferred spelling.

## Testing & Quality
- Lint: `ruff check automation tests` and `ruff format automation tests`.
- Tests: `pytest` (uses sample audio fixtures; Whisper is mocked through unit tests so no network is required).
- CI philosophy: keep each stage deterministic and record any manual gaps in `handoff.md`.

## Roadmap
See `plan.md` and `TODO.md` for upcoming automation stages (export validation, show notes, artwork, publish). Each milestone adds a new CLI, config schema, fixtures, and tests so operators can trust the automation before adding heavier AI agents or MCP integrations.
