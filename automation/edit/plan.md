# Edit Stage Plan

## Purpose
Transform ingest outputs into a polished, publish-ready edit by combining deterministic audio processing with AI-assisted review and decision support.

## Inputs from Ingest
- Raw audio per source track (WAV/FLAC) and a synced multitrack mix if available.
- Ingest metadata (episode title, guests, timestamps, show notes draft, recording environment notes).
- Transcript(s) with timestamps (per-speaker diarization if available).
- Detected issues (clipping, dropouts, long silences) and any ingest QA report.

## Outputs
- Edited master audio (WAV) and a delivery-ready mix (MP3).
- Edit decision list (EDL) or JSON cut list for reproducibility.
- Cleaned transcript aligned to final edit.
- Change log/summary for human review.

## Sub-Stages and Module Layout
Place edit automation under `automation/edit/` with the following modules:

1. `automation/edit/plan.md`
   - This document describing the workflow and decision points.

2. `automation/edit/config.py`
   - Dataclasses for edit settings (targets for LUFS, noise reduction thresholds, silence trim rules).

3. `automation/edit/analysis.py`
   - Audio analysis helpers (levels, silence detection, clipping detection, VAD).

4. `automation/edit/cuts.py`
   - Build and manipulate cut lists, apply trimming, remove long silences, and drop filler segments based on guidance.

5. `automation/edit/ai_guidance.py`
   - LLM-powered suggestions (filler removal candidates, content-based cut suggestions, chapter boundaries).

6. `automation/edit/mix.py`
   - Leveling, normalization, compression, and basic EQ chains.

7. `automation/edit/transcript_sync.py`
   - Align transcript edits with cut lists; produce cleaned transcript.

8. `automation/edit/export.py`
   - Final render outputs, metadata embedding, and checksum generation.

9. `automation/edit/cli.py`
   - CLI entry point and orchestration for dry-run or full processing.

## AI-Assisted Steps
AI should assist at multiple points to reduce manual review time while keeping deterministic, reversible edits.

1. **Filler/Disfluency Candidate Detection**
   - Input: transcript with timestamps.
   - Output: suggested removal segments with confidence and context.
   - Human review: accept/reject per segment.

2. **Content-Based Cut Suggestions**
   - Identify off-topic tangents or repetitive sections using transcript clustering.
   - Output: candidate cut ranges (no auto-delete without review).

3. **Chapter/Segment Boundary Detection**
   - Detect topic shifts and propose chapter markers.
   - Output: candidate markers for show notes or chapter metadata.

4. **Quality Issue Summarization**
   - Summarize where audio artifacts, overlaps, or long pauses occur.
   - Output: review checklist to speed human QA.

## AI Technologies and Constraints
### Local, No-GPU Options
- **Silence/VAD**: WebRTC VAD or Pyannote-free VAD for segmentation (CPU friendly).
- **Transcript alignment**: Whisper.cpp for alignment or Whisper timestamp re-alignment.
- **Audio processing**: FFmpeg + SoX for deterministic trims and filters.

### ChatGPT Pro / OpenAI-Compatible Options (No Extra Charges)
Use ChatGPT Pro interactively and via MCPs that route through the ChatGPT Pro account without additional API billing.
- **LLM suggestions**: prompt the model with transcript snippets for cut candidates and summaries.
- **Transcript cleanup**: normalize punctuation, remove false starts, map edits to timestamps.
- **Chaptering**: LLM proposes topics and time ranges.

### OpenAI APIs and MCPs
- Prefer MCPs that can leverage the ChatGPT Pro account without additional billing. These can be used for:
  - Transcript-based editorial suggestions.
  - Summaries and chapter outlines.
  - QA checklists.
- If a stable MCP/API is low cost but not covered by Pro access (e.g., a paid diarization API), **ask before using**.

### If Additional APIs Are Considered
- Speaker diarization APIs (e.g., commercial diarization services) can be more accurate but may be paid.
- If proposed, request approval before integration.

## Edit Flow (High-Level)
1. **Load Inputs**: ingest metadata, audio stems, and transcript(s).
2. **Analyze Audio**: levels, clipping, long pauses, overlaps.
3. **Generate AI Guidance**: filler candidates, topic boundaries, QA checklist.
4. **Build Cut List**: consolidate silence trims + AI suggestions + rules.
5. **Apply Edits**: trim audio, smooth transitions, normalize loudness.
6. **Sync Transcript**: remove text corresponding to cuts.
7. **Export**: final WAV + MP3, metadata, checksums.
8. **Report**: summary of edits and review notes.

## MCP & API Integration Notes
- MCPs should be configured to operate without external billing and must support Pro-based access.
- Log which MCPs were used and for what purpose in the edit report.
- If an MCP or API would incur extra charges, request approval before integration.

## CLI Entry Point
Suggested command:
```
python -m automation.edit.cli --input <ingest_dir> --output <edit_dir> --dry-run
```

## Test Strategy
- Add tests under `tests/edit/` mirroring module names.
- Use small, deterministic audio fixtures and short transcripts.
- For CPU-only environments, keep fixtures small and limit runtime.
