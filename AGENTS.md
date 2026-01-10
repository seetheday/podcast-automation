# Repository Guidelines

## Project Structure & Module Organization
Root documentation (`Original-manual-workflow.md`, `TODO.md`, `HANDOFF.md`) describes the production journey and must stay updated whenever steps evolve. Place Python automation code under `automation/` with subpackages for each stage (`ingest`, `edit`, `export`, `transcript`, `notes`, `artwork`, `publish`) so that workflows can be composed stage-by-stage. Shared helpers belong in `automation/common`. Put sample media and templates under `assets/audio/<episode>` and `assets/artwork/`; track large binaries with Git LFS and keep private masters outside the repo. Tests mirror the tree inside `tests/<stage>` so readers can jump between implementation and coverage. Configuration files (YAML or TOML) reside in `configs/` and should never contain credentials.

## Build, Test, and Development Commands
Use Python 3.11+. Create an environment with `python -m venv .venv && source .venv/bin/activate`, then install deps via `pip install -r requirements.txt` once it lands. Run `ruff check automation` before committing to enforce lint rules, and `ruff format automation tests` to normalize style. Execute `pytest tests` for the full suite; narrow scope with `pytest tests/transcript -k timestamps` when iterating. The staging CLI for a component should be runnable, e.g. `python -m automation.ingest.sync --dry-run assets/audio/samples/*.wav`, so reviewers can exercise a single stage quickly.

## Coding Style & Naming Conventions
Follow PEP 8 with four-space indents, type hints, and dataclasses for immutable configs. Modules and functions use `snake_case`, classes `PascalCase`, and CLI entry points `hyphen-case` (`generate-notes`). Keep functions under 40 lines by extracting helpers. Use descriptive filenames such as `ingest_sync.py` instead of `utils.py`. Add clear comments for all functions, classes, and related APIs that explain what they do and how to use them.

## Testing Guidelines
Rely on `pytest` with fixtures for temporary audio directories. Name tests `test_<behavior>` and include scenario tags in docstrings ("merge overlapping speech"). Add regression fixtures whenever you fix an editing defect. Target >80% coverage for new modules; if audio-heavy components are hard to test, document the gap in `HANDOFF.md` and provide a deterministic sample input.

## Commit & Pull Request Guidelines
Commits follow the existing imperative, present-tense style ("Add ingest scaffolding"). Keep them scoped to a single stage, referencing tickets like `#12` when applicable. Pull requests need: purpose summary, checklist of affected pipeline stages, test evidence (`pytest tests/export`), and attachments or screenshots when UI or artwork generation changes behavior. Mention any secrets or environment variables required for reviewers so staging remains reproducible.

## Security & Configuration Tips
Never commit API keys or other secrets. Store device-specific settings in `.env` (already ignored) and document required names in `HANDOFF.md`. 
