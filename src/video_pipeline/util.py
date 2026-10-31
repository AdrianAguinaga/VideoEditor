"""Errors, identifiers, safe paths, hashing and YAML I/O shared by every layer."""

from __future__ import annotations

import hashlib
import os
import re
import unicodedata
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

ID_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
_ID_RE = re.compile(ID_PATTERN)


class PipelineError(Exception):
    """Base error. `exit_code` is what the CLI returns; `hint` is the actionable next step."""

    exit_code = 1

    def __init__(self, message: str, hint: str | None = None) -> None:
        super().__init__(message)
        self.hint = hint


class UsageError(PipelineError):
    exit_code = 2  # bad arguments, ambiguity, already exists


class NotConfigured(PipelineError):
    exit_code = 3  # missing workspace, tool or model


class ToolError(PipelineError):
    exit_code = 4  # an external tool (ffmpeg, ffprobe, ASR) failed


class ValidationFailed(PipelineError):
    exit_code = 5  # data contract or invariant violated


class LockedError(PipelineError):
    exit_code = 6  # another writer holds the video lock


def check_id(value: str, what: str = "id") -> str:
    if not _ID_RE.match(value) or len(value) > 64:
        raise UsageError(
            f"invalid {what} {value!r}",
            hint="use lowercase letters, digits and single hyphens, e.g. 'clase-001'",
        )
    return value


def slugify(text: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
    return slug[:64].rstrip("-") or "item"


def safe_join(root: Path, *parts: str | Path) -> Path:
    """Join below `root`, rejecting traversal and any symlink/junction on the way."""
    root = root.resolve()
    candidate = root.joinpath(*parts)
    current = root
    for part in candidate.relative_to(root).parts if candidate.is_relative_to(root) else ():
        current = current / part
        if current.is_symlink() or (hasattr(current, "is_junction") and current.is_junction()):
            raise ValidationFailed(f"refusing symlink/junction in path: {current}")
    resolved = candidate.resolve()
    if not resolved.is_relative_to(root):
        raise ValidationFailed(f"path escapes {root}: {Path(*map(str, parts))}")
    return resolved


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def load_yaml(path: Path) -> Any:
    try:
        with path.open(encoding="utf-8") as fh:
            return yaml.safe_load(fh)
    except FileNotFoundError:
        raise NotConfigured(f"missing file: {path}") from None
    except yaml.YAMLError as exc:
        raise ValidationFailed(f"invalid YAML in {path}: {exc}") from None


def dump_yaml(data: Any) -> str:
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=100)


def write_yaml(path: Path, data: Any) -> None:
    """Atomic replace: readers never see a half-written file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(dump_yaml(data), encoding="utf-8")
    os.replace(tmp, path)


def write_new_yaml(path: Path, data: Any) -> None:
    """Create-only write; fails instead of overwriting history."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as fh:
        fh.write(dump_yaml(data))
