from automation.transcript.generate import apply_word_replacements, replace_words


def test_replace_words_handles_case() -> None:
    replacements = {"christina": "christina"}
    assert replace_words("christina", replacements) == "christina"
    assert replace_words("Christina", replacements) == "Christina"
    assert replace_words("CHRISTINA", replacements) == "CHRISTINA"


def test_apply_word_replacements_updates_segments() -> None:
    segments = [{"text": "Hi Kristina"}]
    replacements = {"kristina": "Christina"}
    apply_word_replacements(segments, replacements)
    assert segments[0]["text"] == "Hi Christina"
