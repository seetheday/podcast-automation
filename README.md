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

## Architecture Diagrams
`docs/architecture/workspace.dsl` captures the C4 story for the Maple History automation stack. Use Structurizr Lite to view/edit:

```bash
docker run --rm -it \
  -p 8081:8080 \
  -v "$(pwd)/docs/architecture:/usr/local/structurizr" \
  structurizr/lite
```

Visit `http://localhost:8081`, open `workspace.dsl`, and export PNG/SVG. `docs/architecture/README.md` covers Structurizr CLI usage and maintenance expectations.

### Visual reference
The repo tracks the latest diagrams (and their legend keys) so reviewers can reference them quickly:

1. **System context** – producers/engineers, Syncthing/Reaper, Whisper, Acast/Sanity.
   ![Automation Context Diagram](docs/architecture/structurizr-1-context.png)
   ![Context Diagram Key](docs/architecture/structurizr-1-context-key.png)

2. **Container view** – ingest/edit/export/transcript/notes/artwork/publish CLIs plus shared stores (`configs/`, `assets/`, `outputs/`) and docs/tests surfaces.
   ![Automation Container Diagram](docs/architecture/structurizr-1-containers.png)
   ![Container Diagram Key](docs/architecture/structurizr-1-containers-key.png)

3. **Edit component view** – the orchestration, config, mixing, analysis, cuts, transcript sync, AI guidance, and export pieces inside `automation.edit`.
   ![Edit Component Diagram](docs/architecture/structurizr-1-edit-components.png)
   ![Edit Component Diagram Key](docs/architecture/structurizr-1-edit-components-key.png)
