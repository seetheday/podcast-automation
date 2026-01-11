"""Catalog recordings and renders that already exist in the synced Reaper workspace."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import re
from pathlib import Path
from typing import Any, Sequence

import tomllib

DEFAULT_SOURCE_ROOT = Path.home() / "Reaper" / "MacBook"
DEFAULT_RENDER_DIR = DEFAULT_SOURCE_ROOT / "final audio"
DEFAULT_EXTENSIONS = (".wav",)


@dataclass(frozen=True)
class Recording:
    """A single synced recording."""

    path: Path

    @property
    def size_bytes(self) -> int:
        return self.path.stat().st_size


@dataclass(frozen=True)
class RenderInfo:
    """Information about a rendered MP3 stored in the final audio directory."""

    path: Path | None
    duplicates: tuple[Path, ...] = ()

    @property
    def status(self) -> str:
        if self.path and not self.duplicates:
            return "found"
        if self.duplicates:
            return "duplicate"
        return "missing"


@dataclass(frozen=True)
class Episode:
    """An episode folder containing media already synced via Syncthing."""

    name: str
    media_dir: Path
    recordings: list[Recording]
    render: RenderInfo

    @property
    def total_size(self) -> int:
        return sum(recording.size_bytes for recording in self.recordings)


@dataclass
class IngestConfig:
    """Configuration describing where synced sessions live."""

    source_root: Path = DEFAULT_SOURCE_ROOT
    render_dir: Path = DEFAULT_RENDER_DIR
    extensions: tuple[str, ...] = DEFAULT_EXTENSIONS

    def normalized_extensions(self) -> tuple[str, ...]:
        return tuple(ext.lower() for ext in self.extensions)


def expand_path(value: str | Path) -> Path:
    return Path(value).expanduser().resolve()


def load_config_from_file(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    with path.open("rb") as handle:
        return tomllib.load(handle)


def parse_extensions(raw: str | Sequence[str] | None) -> tuple[str, ...] | None:
    if raw is None:
        return None
    if isinstance(raw, str):
        tokens = [token.strip() for token in raw.split(",") if token.strip()]
    else:
        tokens = [str(token).strip() for token in raw if str(token).strip()]
    if not tokens:
        raise ValueError("At least one extension must be provided")
    normalized = [token if token.startswith(".") else f".{token}" for token in tokens]
    return tuple(ext.lower() for ext in normalized)


def build_ingest_config(
    *,
    config_path: Path | None,
    source_override: Path | None,
    render_override: Path | None,
    extensions_override: tuple[str, ...] | None,
) -> IngestConfig:
    settings = load_config_from_file(config_path)
    config = IngestConfig()

    source_root = settings.get("source_root")
    render_dir = settings.get("render_dir")
    extensions = settings.get("extensions")

    if source_root:
        config.source_root = expand_path(source_root)
    if render_dir:
        config.render_dir = expand_path(render_dir)
    if extensions:
        parsed = parse_extensions(extensions)
        if parsed:
            config.extensions = parsed

    if source_override is not None:
        config.source_root = expand_path(source_override)
    if render_override is not None:
        config.render_dir = expand_path(render_override)
    if extensions_override is not None:
        config.extensions = extensions_override

    return config


def discover_episodes(config: IngestConfig, *, episode_filter: str | None = None) -> list[Episode]:
    if not config.source_root.exists():
        raise FileNotFoundError(f"Source root not found: {config.source_root}")

    episodes: list[Episode] = []
    for candidate in sorted(p for p in config.source_root.iterdir() if p.is_dir()):
        if episode_filter and candidate.name != episode_filter:
            continue
        media_dir = candidate / "Media"
        if not media_dir.is_dir():
            continue
        recordings = list_recordings(media_dir, config)
        if recordings:
            render = locate_render(candidate.name, config)
            episodes.append(
                Episode(name=candidate.name, media_dir=media_dir, recordings=recordings, render=render)
            )
    return episodes


def list_recordings(media_dir: Path, config: IngestConfig) -> list[Recording]:
    recordings: list[Recording] = []
    extensions = config.normalized_extensions()
    for path in media_dir.iterdir():
        if path.is_file() and path.suffix.lower() in extensions:
            recordings.append(Recording(path=path))
    return sorted(recordings, key=lambda rec: rec.path.name)


def normalize_label(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def locate_render(episode_name: str, config: IngestConfig) -> RenderInfo:
    render_dir = config.render_dir
    if not render_dir.exists():
        return RenderInfo(path=None)

    expected_key = normalize_label(episode_name)
    matches: list[Path] = []
    for candidate in render_dir.glob("*.mp3"):
        if normalize_label(candidate.stem) == expected_key:
            matches.append(candidate)

    if not matches:
        return RenderInfo(path=None)
    if len(matches) == 1:
        return RenderInfo(path=matches[0])
    return RenderInfo(path=None, duplicates=tuple(matches))


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__ or "ingest.sync")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/ingest.toml"),
        help="Optional TOML config file describing source/render directories",
    )
    parser.add_argument("--source-root", type=Path, help="Override source root directory", dest="source_root")
    parser.add_argument("--render-dir", type=Path, help="Override render directory", dest="render_dir")
    parser.add_argument(
        "--extensions",
        help="Comma separated list of accepted extensions (default: .wav)",
    )
    parser.add_argument("--episode", help="Only inspect the specified episode (folder name)")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    config = build_ingest_config(
        config_path=args.config,
        source_override=args.source_root,
        render_override=args.render_dir,
        extensions_override=parse_extensions(args.extensions) if args.extensions else None,
    )

    episodes = discover_episodes(config, episode_filter=args.episode)
    if not episodes:
        print("No episodes found. Ensure the source root contains <episode>/Media directories.")
        return 1

    for episode in episodes:
        print(f"Episode: {episode.name}")
        print(f"  Media dir: {episode.media_dir}")
        print(f"  Files: {len(episode.recordings)}")
        for recording in episode.recordings:
            print(f"    - {recording.path.name} ({recording.size_bytes} bytes)")
        if episode.render.status == "found" and episode.render.path:
            print(f"  Render: FOUND -> {episode.render.path}")
        elif episode.render.status == "duplicate":
            print("  Render: DUPLICATE matches detected:")
            for dup in episode.render.duplicates:
                print(f"    * {dup}")
        else:
            print(f"  Render: MISSING in {config.render_dir}")
        print()

    print(
        f"Discovered {len(episodes)} episode(s) under {config.source_root}. "
        f"Render output will remain at {config.render_dir}."
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
