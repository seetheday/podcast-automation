import pytest

from automation.edit.cuts import CutSegment
from automation.edit.transcript_sync import (
    TranscriptDocument,
    TranscriptSegment,
    build_noise_cuts,
    apply_cuts_to_transcript,
    find_phrase_timestamp,
    normalize_text,
)


def test_find_phrase_timestamp_matches_phrase() -> None:
    document = TranscriptDocument(
        text="",
        segments=(
            TranscriptSegment(start_s=0.0, end_s=1.0, text="crowd noise"),
            TranscriptSegment(start_s=1.2, end_s=2.5, text="Hi, and welcome back to Maple History"),
        ),
    )

    timestamp = find_phrase_timestamp(document, ["Hi, and Welcome back to Maple History"])
    assert timestamp == 1.2


def test_build_noise_cuts_aligns_with_host_trim() -> None:
    document = TranscriptDocument(
        text="",
        segments=(
            TranscriptSegment(start_s=0.2, end_s=0.4, text="laughing"),
            TranscriptSegment(start_s=1.0, end_s=1.2, text="host speaks"),
        ),
    )

    cuts = build_noise_cuts(
        document,
        keywords=["laugh"],
        host_trim_s=0.0,
        intro_delay_s=6.836,
        padding_s=0.05,
    )

    assert len(cuts) == 1
    cut = cuts[0]
    assert cut.reason == "transcript_noise"
    assert cut.start_s == pytest.approx(6.986, abs=0.001)
    assert cut.end_s == pytest.approx(7.286, abs=0.001)


def test_normalize_text_simplifies_input() -> None:
    assert normalize_text("Hi!!!") == "hi"


def test_apply_cuts_to_transcript_removes_overlap() -> None:
    document = TranscriptDocument(
        text="Hi there",
        segments=(
            TranscriptSegment(start_s=0.0, end_s=0.5, text="Hi"),
            TranscriptSegment(start_s=0.5, end_s=1.0, text="there"),
        ),
    )
    cuts = [CutSegment(start_s=6.9, end_s=7.2, reason="trim")]

    result = apply_cuts_to_transcript(
        document,
        cuts,
        host_trim_s=0.0,
        intro_delay_s=6.836,
    )

    assert result.removed_segments == 1
    assert result.updated_text.strip() == "there"
