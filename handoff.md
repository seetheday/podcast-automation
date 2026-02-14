# Current Status

- Edit stage auto-generates Whisper transcripts (with enforced word replacements) when none are provided, aligns the host “Hi…” cue at 6.836 s, removes clap/laugh moments, and keeps host + guest tracks in sync by applying identical trims/cuts to both streams; stems are exported as `edited-master-host.wav` / `edited-master-guest.wav` for manual touch-ups.
- Transcript utilities now trim the textual transcript too: `apply_cuts_to_transcript` realigns segment timestamps (host trim + intro delay) and removes any segments overlapping the final cut list so `transcript.txt` mirrors the audio.
- Mixing/CLI/export/report code updated to handle the richer mix result and per-track trimming, while transcript assets, metering, and Whisper config modules (with `configs/transcript.example.toml`) document how to configure spelling overrides.
- Full test suite (`PYTHONDONTWRITEBYTECODE=1 pytest`) covers ingest, edit mixing, transcript sync, metering, and transcription helpers.

# Recent Prompts
1. "I want this codebase to generate the timestamped transcript..."
2. "The host audio is now coming in at close to the right spot..."
3. "Earlier you suggested... Replace the placeholder apply_cuts_to_transcript..."

# Suggested Next Steps
- Provide sample transcript JSON fixtures for contributors without Whisper installed, or guard the CLI with a clearer error when Whisper/torch isn’t available.
- Surface configurable phrase/keyword lists in a TOML file so future episodes can tweak alignment without code edits.
- Document the new stem exports and transcript-trimming flow in README/AGENTS (including ffmpeg + torch install tips).

# Agentic Stage Readiness (for stakeholder conversations)

The current repo is still in a **workflow automation foundation** phase, not a full agentic orchestration phase. The existing CLIs are deterministic, stage-specific building blocks that make the pipeline reproducible and testable before adding higher-autonomy decision loops.

## Recommended plan for the agentic stage

When we promote to an agentic architecture, prioritize OpenAI APIs so the team can stay on one paid platform:

1. **Primary orchestration model**: OpenAI Responses API (`gpt-5`/`gpt-4.1` class) with tool calling.
2. **Pipeline control loop**: a thin planner/executor that can run stage CLIs (`ingest`, `edit`, `export`, `transcript`, `notes`, `artwork`, `publish`) as tools.
3. **State + audit trail**: persist run goals, intermediate decisions, tool outputs, and final artifacts to `outputs/` plus structured JSON logs.
4. **Human-in-the-loop gates**: require approval checkpoints before irreversible actions (publishing, metadata pushes, artwork replacement).
5. **Guardrails**: strict prompt templates, schema validation for tool arguments, max-step/time budgets, and rollback/retry policies.

## Suggested implementation sequence

- **Phase A (next)**: keep deterministic stage CLIs as-is; add machine-readable output contracts where missing.
- **Phase B**: add a local orchestrator command (for example, `python -m automation.agent.run`) that calls stage CLIs via tool wrappers.
- **Phase C**: add policy gates and reviewer approvals, then connect outbound integrations (Acast/CMS) behind feature flags.

This sequencing keeps quality and editorial authenticity first while making it easier to explain internally: *we are deliberately not fully agentic yet; we are preparing the substrate so agentic behavior is safe and useful when introduced*.
