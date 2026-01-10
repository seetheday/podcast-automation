# TODO

## Critical path (run tests with real sample inputs)
- [HUMAN] Add sample original `.wav` files under `assets/audio/<episode>`.
- [HUMAN] Create 60-second sample files in Reaper (must be under 50 MB).
- [HUMAN] Add a music bed file under `assets/audio/<episode>` (or `assets/audio/music` if preferred).
- [HUMAN] Add sample output files to the repo for comparison/regression checks.
- [HUMAN] Track any large binaries with Git LFS and keep private masters outside the repo.
- [HUMAN] Document required environment variables (if any) in `HANDOFF.md`.
- [CAN HELP] Ensure `requirements.txt` is installed in a Python 3.11+ venv for testing.
- [CAN HELP] Create/extend `pytest` fixtures under `tests/<stage>` to point at the sample inputs.
- [CAN HELP] Run `pytest tests` (or stage-specific subsets) and record results.

## Later / backlog
- [CAN HELP] Set up Codex code review in GitHub.
- [CAN HELP] Look into MCPs for better transcription with timestamps.
  - [CAN HELP] Explore adding transcription rules (e.g., "Christina" vs "Kristina").
- [CAN HELP] Create overall `plan.md`.
- [CAN HELP] Create 1st component `plan.md`.
