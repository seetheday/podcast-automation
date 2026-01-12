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
