"""Workspace layout, series/video identities, config precedence and the per-video writer lock."""

from __future__ import annotations

import contextlib
import json
import os
import re
import socket
import sys
import unicodedata
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .contracts import (
    AssetRegistry,
    InputInventory,
    Model,
    Profile,
    SeriesConfig,
    Settings,
    VideoConfig,
    WorkspaceConfig,
)
from .util import (
    LockedError,
    NotConfigured,
    UsageError,
    ValidationFailed,
    check_id,
    load_yaml,
    now_iso,
    safe_join,
    write_yaml,
)

WORKSPACE_FILE = Path("config/workspace.yaml")
VIDEO_DIRS = [
    "inputs/originals",
    "inputs/audio",
    "inputs/slides",
    "inputs/images",
    "inputs/broll",
    "inputs/scripts",
    "manifests",
    "editorial/transcript",
    "editorial/decisions",
    "editorial/timelines",
    "approvals",
    "runs",
]
DEFAULT_PROFILES = {
    "1080p30": Profile(width=1920, height=1080, fps=30),
    "720p30": Profile(width=1280, height=720, fps=30),
}


def parse[M: Model](model: type[M], data: Any, source: Path | str) -> M:
    try:
        return model.model_validate(data)
    except ValidationError as exc:
        raise ValidationFailed(f"{source} does not match the {model.__name__} contract:\n{exc}") from None


def deep_merge(base: dict[str, Any], layer: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in layer.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


@dataclass(frozen=True)
class VideoRef:
    series: str
    video: str
    dir: Path

    @property
    def key(self) -> str:
        return f"{self.series}/{self.video}"


class Workspace:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.config = parse(WorkspaceConfig, load_yaml(self.root / WORKSPACE_FILE), WORKSPACE_FILE)

    @classmethod
    def find(cls, start: Path | None = None) -> Workspace:
        env = os.environ.get("VIDEO_PIPELINE_WORKSPACE")
        here = Path(env) if env else (start or Path.cwd())
        for candidate in [here.resolve(), *here.resolve().parents]:
            if (candidate / WORKSPACE_FILE).is_file():
                return cls(candidate)
        raise NotConfigured(f"no workspace found from {here}", hint="run `video-pipeline init` in the project root")

    # --- paths ---
    def path(self, *parts: str | Path) -> Path:
        return safe_join(self.root, *parts)

    def series_dir(self, series: str) -> Path:
        return self.path("series", check_id(series, "series id"))

    def video_ref(self, series: str, video: str) -> VideoRef:
        return VideoRef(
            series,
            video,
            self.path("series", check_id(series, "series id"), "videos", check_id(video, "video id")),
        )

    # --- catalog / series / videos ---
    def series_ids(self) -> list[str]:
        data = load_yaml(self.path("catalog/series.yaml")) or {}
        return list(data.get("series", []))

    def load_series(self, series: str) -> SeriesConfig:
        path = self.series_dir(series) / "series.yaml"
        if not path.is_file():
            raise UsageError(f"series not found: {series}", hint="see `video-pipeline status`")
        return parse(SeriesConfig, load_yaml(path), path)

    def load_video(self, ref: VideoRef) -> VideoConfig:
        path = ref.dir / "video.yaml"
        if not path.is_file():
            raise UsageError(f"video not found: {ref.key}")
        return parse(VideoConfig, load_yaml(path), path)

    def create_series(self, series: str, title: str) -> Path:
        directory = self.series_dir(series)
        if directory.exists():
            raise UsageError(f"series already exists: {series}")
        directory.mkdir(parents=True)
        for sub in ("assets", "videos"):
            (directory / sub).mkdir()
        write_yaml(directory / "series.yaml", SeriesConfig(id=series, title=title).model_dump(mode="json"))
        (directory / "brief.md").write_text(f"# {title}\n\nPúblico, objetivos y tono de la serie.\n", "utf-8")
        write_yaml(directory / "glossary.yaml", {"terms": []})
        catalog = self.series_ids()
        write_yaml(self.path("catalog/series.yaml"), {"series": [*catalog, series]})
        return directory

    def create_video(self, series: str, video: str, title: str) -> VideoRef:
        config = self.load_series(series)
        ref = self.video_ref(series, video)
        if ref.dir.exists() or video in config.videos:
            raise UsageError(f"video already exists: {ref.key}")
        for sub in VIDEO_DIRS:
            (ref.dir / sub).mkdir(parents=True)
        write_yaml(ref.dir / "video.yaml", VideoConfig(id=video, series=series, title=title).model_dump(mode="json"))
        (ref.dir / "brief.md").write_text(f"# {title}\n\nObjetivo de la clase y requisitos editoriales.\n", "utf-8")
        write_yaml(ref.dir / "manifests/inputs.yaml", InputInventory(video=ref.key).model_dump(mode="json"))
        config.videos.append(video)
        write_yaml(self.series_dir(series) / "series.yaml", config.model_dump(mode="json"))
        return ref

    def all_videos(self) -> list[tuple[SeriesConfig, VideoRef, VideoConfig]]:
        result = []
        for sid in self.series_ids():
            series = self.load_series(sid)
            for vid in series.videos:
                ref = self.video_ref(sid, vid)
                result.append((series, ref, self.load_video(ref)))
        return result

    def resolve(self, query: str) -> VideoRef:
        """Resolve 'serie/video' exactly, or a natural name ('clase 1 contabilidad') if unambiguous."""
        if "/" in query:
            series, _, video = query.partition("/")
            ref = self.video_ref(series, video)
            self.load_video(ref)
            return ref
        tokens = _tokens(query)
        if not tokens:
            raise UsageError("empty video reference")
        matches = []
        for s_cfg, ref, v_cfg in self.all_videos():
            haystack = _tokens(" ".join([s_cfg.id, s_cfg.title, v_cfg.id, v_cfg.title]))
            if all(t in haystack for t in tokens):
                matches.append(ref)
        if len(matches) == 1:
            return matches[0]
        if not matches:
            raise UsageError(f"no video matches {query!r}", hint="see `video-pipeline status`")
        options = ", ".join(m.key for m in matches)
        raise UsageError(f"{query!r} is ambiguous: {options}", hint="use the exact 'serie/video' id")

    # --- per-video manifests ---
    def inventory(self, ref: VideoRef) -> InputInventory:
        path = ref.dir / "manifests/inputs.yaml"
        return parse(InputInventory, load_yaml(path), path)

    def registry(self) -> AssetRegistry:
        path = self.path("assets/registry.yaml")
        return parse(AssetRegistry, load_yaml(path) or {}, path)

    def profile(self, name: str) -> Profile:
        check_id(name.lower(), "profile")
        path = self.path("config/profiles", f"{name}.yaml")
        return parse(Profile, load_yaml(path), path)

    def settings(self, ref: VideoRef, override: dict[str, Any] | None = None) -> Settings:
        """Precedence: workspace defaults < series defaults < video overrides < approved run override."""
        merged = deep_merge({}, self.config.defaults)
        merged = deep_merge(merged, self.load_series(ref.series).defaults)
        merged = deep_merge(merged, self.load_video(ref).overrides)
        merged = deep_merge(merged, override or {})
        return parse(Settings, merged, f"resolved settings for {ref.key}")


_STOPWORDS = {"de", "del", "la", "el", "los", "las", "y", "en", "video", "the", "of"}


def _tokens(text: str) -> set[str]:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    tokens = set()
    for raw in re.split(r"[^a-z0-9]+", ascii_text):
        if not raw or raw in _STOPWORDS:
            continue
        tokens.add(str(int(raw)) if raw.isdigit() else raw)  # "001" and "1" match
        tokens.update(str(int(d)) for d in re.findall(r"\d+", raw))
    return tokens


def init_workspace(root: Path, name: str) -> list[Path]:
    """Create the skeleton. Only creates what is missing; never overwrites user files."""
    root = root.resolve()
    created: list[Path] = []

    def ensure_file(rel: str, data: Any) -> None:
        path = root / rel
        if not path.exists():
            write_yaml(path, data)
            created.append(path)

    for rel in (
        "config/profiles",
        "config/schemas",
        "catalog/views",
        "series",
        "evals",
        "docs/decisions",
        "assets/cortinillas/entrada",
        "assets/cortinillas/salida",
        "assets/cortinillas/transiciones",
        "assets/logos",
        "assets/tipografias",
        "assets/musica",
        "assets/efectos-sonoros",
        "assets/templates",
        ".local/state",
    ):
        path = root / rel
        if not path.exists():
            path.mkdir(parents=True)
            created.append(path)
    ensure_file(str(WORKSPACE_FILE), WorkspaceConfig(name=name).model_dump(mode="json"))
    for pname, profile in DEFAULT_PROFILES.items():
        ensure_file(f"config/profiles/{pname}.yaml", profile.model_dump(mode="json"))
    ensure_file("assets/registry.yaml", AssetRegistry().model_dump(mode="json"))
    ensure_file("catalog/series.yaml", {"series": []})
    return created


# --- writer lock ---------------------------------------------------------------------------------


def pid_alive(pid: int) -> bool:
    if sys.platform == "win32":
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return False
        code = ctypes.c_ulong()
        kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
        kernel32.CloseHandle(handle)
        return code.value == 259  # STILL_ACTIVE
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def lock_state(ref: VideoRef) -> tuple[str, dict[str, Any] | None]:
    """Returns ('free'|'held'|'stale', lock info)."""
    path = ref.dir / ".lock"
    try:
        info = json.loads(path.read_text("utf-8"))
    except FileNotFoundError:
        return "free", None
    except (OSError, ValueError):
        return "stale", {"detail": "unreadable lock file"}
    same_host = info.get("host") == socket.gethostname()
    if same_host and not pid_alive(int(info.get("pid", -1))):
        return "stale", info
    return "held", info


@contextlib.contextmanager
def video_lock(ref: VideoRef, purpose: str) -> Iterator[None]:
    path = ref.dir / ".lock"
    info = {"pid": os.getpid(), "host": socket.gethostname(), "purpose": purpose, "since": now_iso()}
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        state, held = lock_state(ref)
        if state == "stale":
            raise LockedError(
                f"{ref.key} has a stale lock ({held})",
                hint=f"the previous process is gone; run `video-pipeline unlock {ref.key}`",
            ) from None
        raise LockedError(f"{ref.key} is locked by another writer: {held}") from None
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(info, fh)
    try:
        yield
    finally:
        path.unlink(missing_ok=True)


def unlock(ref: VideoRef) -> dict[str, Any] | None:
    state, info = lock_state(ref)
    if state == "held":
        raise LockedError(f"{ref.key} lock is held by a live process: {info}")
    (ref.dir / ".lock").unlink(missing_ok=True)
    return info
