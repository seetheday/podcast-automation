# Current Status

- Ingest CLI (`automation/ingest/sync.py`) now catalogs both WAV recordings and matching renders: it loads defaults pointing to `~/Reaper/MacBook`, reads overrides from `configs/ingest.toml`, discovers `<episode>/Media/*.wav`, and validates whether a rendered MP3 exists in `final audio` (including duplicate detection).
- Added an example config (`configs/ingest.example.toml`) for source/render overrides and kept `configs/ingest.toml` optional.
- Expanded the ingest test suite (`tests/ingest/test_sync.py`) to cover config parsing, episode discovery, render presence, missing renders, and duplicate render detection. All tests pass with `PYTHONDONTWRITEBYTECODE=1 pytest`.
- Sample input audio for automation work lives in `assets/audio/samples` for local testing and fixtures.
- Added the first edit-stage pipeline (`automation/edit/cli.py`) that mixes WAV inputs, trims leading/trailing silence, writes a master WAV + cut list + edit report, and attempts an MP3 encode when `ffmpeg` is available.
- Documented edit-stage configuration keys in `configs/edit.example.toml` (copy to `configs/edit.toml` locally to customize silence trimming behavior).

# Recent Prompts
1. "Given this information is the ingest code correct?"
2. "Make changes 1 & 2 and explain what you mean by optionally validating existing renders in final audio means."
3. "Ok, proceed with creating render validation."

# Suggested Next Steps
- Integrate ingest metadata into downstream automation stages (edit/export) so they can quickly see whether renders exist and decide to overwrite or skip export.
- Document the CLI usage and config format in `README.md` for onboarding.
- Extend render validation with audio-specific checks (duration, LUFS, timestamp) once the export automation is implemented.
- Add real transcript alignment and AI guidance integration once MCP support is wired up for the edit stage.
