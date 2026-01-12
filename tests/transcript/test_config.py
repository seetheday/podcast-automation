from pathlib import Path

from automation.transcript.config import build_transcription_config


def test_build_transcription_config_merges_settings(tmp_path: Path) -> None:
    config_path = tmp_path / "transcript.toml"
    config_path.write_text(
        """
        model_size = "base"
        temperature = 0.25
        [word_replacements]
        christina = "Christina"
        """
    )

    config = build_transcription_config(config_path, {"maple": "Maple"})
    assert config.model_size == "base"
    assert config.temperature == 0.25
    assert config.word_replacements["christina"] == "Christina"
    assert config.word_replacements["maple"] == "Maple"
