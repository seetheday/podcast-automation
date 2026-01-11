from pathlib import Path

from automation.ingest import IngestConfig, build_ingest_config, discover_episodes


def write_toml(path: Path, content: str) -> None:
    """Write TOML content to disk for configuration tests."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def create_wav(path: Path, content: bytes = b"data") -> None:
    """Create a small WAV placeholder file for ingest tests."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def create_mp3(path: Path, content: bytes = b"ID3") -> None:
    """Create a small MP3 placeholder file for ingest tests."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def test_build_ingest_config_reads_toml(tmp_path: Path) -> None:
    """Scenario: read ingest config from TOML."""
    config_path = tmp_path / "configs" / "ingest.toml"
    write_toml(
        config_path,
        """
        source_root = "{root}"
        render_dir = "{render}"
        extensions = [".wav", "flac"]
        """.format(root=tmp_path / "sessions", render=tmp_path / "renders"),
    )

    config = build_ingest_config(
        config_path=config_path,
        source_override=None,
        render_override=None,
        extensions_override=None,
    )

    assert config.source_root == (tmp_path / "sessions")
    assert config.render_dir == (tmp_path / "renders")
    assert config.extensions == (".wav", ".flac")


def test_build_ingest_config_overrides_cli(tmp_path: Path) -> None:
    """Scenario: override TOML settings with CLI inputs."""
    config_path = tmp_path / "configs" / "ingest.toml"
    write_toml(
        config_path,
        'source_root = "/tmp/ignored"\nrender_dir = "/tmp/ignored"\n',
    )

    override_source = tmp_path / "custom"
    override_render = tmp_path / "final"
    config = build_ingest_config(
        config_path=config_path,
        source_override=override_source,
        render_override=override_render,
        extensions_override=(".wav",),
    )

    assert config.source_root == override_source.resolve()
    assert config.render_dir == override_render.resolve()


def test_discover_episodes_lists_media_dirs(tmp_path: Path) -> None:
    """Scenario: list episodes with media folders."""
    root = tmp_path / "Reaper" / "MacBook"
    episode_dir = root / "Huron Carol" / "Media"
    create_wav(episode_dir / "01-host.wav", b"wave")
    create_wav(episode_dir / "02-guest.wav", b"wave")
    # This directory should be ignored because it lacks Media
    (root / "README").mkdir(parents=True)

    render_dir = root / "final audio"
    create_mp3(render_dir / "Huron Carol.mp3")

    config = IngestConfig(source_root=root, render_dir=render_dir)
    episodes = discover_episodes(config)

    assert len(episodes) == 1
    episode = episodes[0]
    assert episode.name == "Huron Carol"
    assert len(episode.recordings) == 2
    assert episode.recordings[0].path.name == "01-host.wav"
    assert episode.render.status == "found"
    assert episode.render.path == render_dir / "Huron Carol.mp3"


def test_discover_episodes_filters_by_name(tmp_path: Path) -> None:
    """Scenario: filter episodes by name."""
    root = tmp_path / "Reaper" / "MacBook"
    create_wav(root / "EpisodeA" / "Media" / "a.wav")
    create_wav(root / "EpisodeB" / "Media" / "b.wav")

    config = IngestConfig(source_root=root, render_dir=root / "final audio")
    episodes = discover_episodes(config, episode_filter="EpisodeB")

    assert len(episodes) == 1
    assert episodes[0].name == "EpisodeB"


def test_discover_episodes_reports_missing_render(tmp_path: Path) -> None:
    """Scenario: report missing render output."""
    root = tmp_path / "Reaper" / "MacBook"
    create_wav(root / "EpisodeA" / "Media" / "a.wav")
    config = IngestConfig(source_root=root, render_dir=root / "final audio")

    episode = discover_episodes(config)[0]
    assert episode.render.status == "missing"
    assert episode.render.path is None


def test_discover_episodes_reports_duplicate_renders(tmp_path: Path) -> None:
    """Scenario: report duplicate render outputs."""
    root = tmp_path / "Reaper" / "MacBook"
    render_dir = root / "final audio"
    create_wav(root / "Episode A" / "Media" / "a.wav")
    create_mp3(render_dir / "Episode-A.mp3")
    create_mp3(render_dir / "Episode A.mp3")

    config = IngestConfig(source_root=root, render_dir=render_dir)
    episode = discover_episodes(config)[0]

    assert episode.name == "Episode A"
    assert episode.render.status == "duplicate"
    assert len(episode.render.duplicates) == 2
