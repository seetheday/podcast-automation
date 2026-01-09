# Automation Package

Each subpackage represents a pipeline stage:

- `ingest`: sync and validate raw mono WAVs from Syncthing drops.
- `edit`: DAW preparation (normalization, gating, clip cleanup helpers).
- `export`: rendering and LUFS verification utilities.
- `transcript`: Whisper/OpenAI transcript + timestamp alignment helpers.
- `notes`: show notes summarization scripts and prompt templates.
- `artwork`: episode artwork templating plus asset metadata management.
- `publish`: integrations with Acast and the website CMS.
- `common`: shared abstractions (logging, data models, file IO).

Add component CLIs under their stage (e.g., `ingest/sync.py`) and expose entry points via `python -m automation.ingest.sync`.
