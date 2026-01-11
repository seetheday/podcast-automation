# Automation Plan

## Goals
- Incrementally automate the podcast production workflow while preserving the manual process quality bar.
- Deliver each stage as a runnable CLI with deterministic inputs/outputs for easy review and testing.
- Keep the workflow reproducible with clear configuration and environment documentation.

## Scope (Single-Workflow, Lean)
- Focus on a single end-to-end production pipeline (one show, one host/guest format).
- Optimize for reliability, repeatability, and clarity over scale.
- Use fixtures and sample inputs to validate each stage.

## Milestones

### M1: Ingest Foundation (Complete)
- Build ingest CLI that catalogs raw WAVs and rendered MP3s.
- Validate episode structure and detect missing/duplicate renders.
- Ensure config override support via `configs/ingest.toml`.

### M2: Edit Automation (Next)
- Define a minimal edit pipeline to normalize, trim, and align tracks.
- Export deterministic edit artifacts suitable for regression tests.
- Document any manual exceptions or gaps in `handoff.md`.

### M3: Export + Render Validation
- Automate final render output validation (duration, LUFS, peak).
- Store render metadata for downstream stages.
- Add tests with deterministic sample audio.

### M4: Transcript + Notes
- Automate transcript generation and any post-processing rules.
- Produce episode notes and metadata stubs suitable for publishing.
- Add tests for transcript output format and timestamps.

### M5: Artwork + Publish
- Generate artwork from templates and metadata.
- Automate publishing steps (Acast + CMS entry creation).
- Verify scheduling alignment between audio and CMS entries.

## Deliverables by Stage
- CLI entry point (e.g., `python -m automation.<stage>.<command> --help`).
- Config file schema (TOML/YAML) in `configs/`.
- Tests and fixtures in `tests/<stage>`.
- Updates to `handoff.md` for gaps or environment requirements.

## Quality Gates
- `ruff check automation` before commit.
- `ruff format automation tests` for consistent formatting.
- `pytest tests` (or stage-specific subsets) with recorded results.

## Risks / Dependencies
- Audio processing accuracy (LUFS/peak normalization) requires reliable tooling.
- Transcription quality and timestamps may vary with model updates.
- External publishing services (Acast, CMS) may require stable APIs or credentials.

## Operating Rhythm (Lightweight)
- Update this plan when milestones shift.
- Keep `TODO.md` as the active backlog.
- Record status and open gaps in `handoff.md` after each milestone.
