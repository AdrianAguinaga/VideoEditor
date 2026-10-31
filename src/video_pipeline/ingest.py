"""Ingest video inputs and register shared assets: copy, verify hash, never touch the original."""

from __future__ import annotations

import os
import shutil
import stat
from pathlib import Path
from typing import get_args

from .contracts import AssetRecord, InputRecord, InputRole
from .media import probe
from .util import UsageError, ValidationFailed, check_id, now_iso, sha256_file, slugify, write_yaml
from .workspace import VideoRef, Workspace, video_lock

_DEFAULT_ROLE: dict[str, InputRole] = {"video": "originals", "audio": "audio", "image": "images"}


def _copy_verified(src: Path, dest: Path, expected_sha: str) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(f".{dest.name}.partial")
    shutil.copy2(src, tmp)
    if sha256_file(tmp) != expected_sha:
        tmp.unlink()
        raise ValidationFailed(f"copy of {src.name} does not match its source hash")
    os.replace(tmp, dest)
    os.chmod(dest, stat.S_IREAD)  # ingested originals are immutable


def _check_source(src: Path) -> Path:
    if src.is_symlink():
        raise ValidationFailed(f"refusing to ingest a symlink: {src}")
    if not src.is_file():
        raise UsageError(f"file not found: {src}")
    return src.resolve()


def ingest(
    ws: Workspace, ref: VideoRef, src: Path, input_id: str | None = None, role: InputRole | None = None
) -> InputRecord:
    if role is not None and role not in get_args(InputRole):
        raise UsageError(f"invalid role {role!r}", hint=f"one of: {', '.join(get_args(InputRole))}")
    src = _check_source(src)
    media = probe(src)  # rejects corrupt or non-media files before anything is copied
    source_sha = sha256_file(src)
    with video_lock(ref, "ingest"):
        inventory = ws.inventory(ref)
        new_id = check_id(input_id or slugify(src.stem), "input id")
        for existing in inventory.inputs:
            if existing.sha256 == source_sha:
                raise UsageError(f"{src.name} is already ingested as {existing.id!r}")
            if existing.id == new_id:
                raise UsageError(f"input id {new_id!r} already used", hint="pass --id")
        chosen_role = role or _DEFAULT_ROLE[media.kind]
        rel = Path("inputs", chosen_role, f"{new_id}{src.suffix.lower()}")
        _copy_verified(src, ref.dir / rel, source_sha)
        if sha256_file(src) != source_sha:
            raise ValidationFailed(f"source {src} changed during ingest")
        record = InputRecord(
            id=new_id,
            role=chosen_role,
            original_name=src.name,
            path=rel.as_posix(),
            sha256=source_sha,
            size_bytes=src.stat().st_size,
            ingested_at=now_iso(),
            media=media,
        )
        inventory.inputs.append(record)
        write_yaml(ref.dir / "manifests/inputs.yaml", inventory.model_dump(mode="json"))
    return record


def register_asset(
    ws: Workspace,
    src: Path,
    asset_id: str,
    version: int,
    kind: str,
    license: str,
    permissions: str,
    role: str | None = None,
    synthetic: bool = False,
) -> AssetRecord:
    """Each id@version is immutable; changing a cortinilla means registering a new version."""
    src = _check_source(src)
    registry = ws.registry()
    check_id(asset_id, "asset id")
    if any(a.id == asset_id and a.version == version for a in registry.assets):
        raise UsageError(f"asset {asset_id}@{version} already registered", hint="register a new --version")
    media = probe(src) if kind in ("cortinilla", "music", "sfx", "logo", "image") else None
    sha = sha256_file(src)
    folder = {
        "cortinilla": f"cortinillas/{role or 'entrada'}",
        "logo": "logos",
        "image": "imagenes",
        "font": "tipografias",
        "music": "musica",
        "sfx": "efectos-sonoros",
        "template": "templates",
    }[kind]
    rel = Path("assets", folder, asset_id, f"v{version}{src.suffix.lower()}")
    _copy_verified(src, ws.path(rel), sha)
    record = AssetRecord.model_validate(
        {
            "id": asset_id,
            "version": version,
            "kind": kind,
            "role": role,
            "path": rel.as_posix(),
            "sha256": sha,
            "license": license,
            "permissions": permissions,
            "synthetic_fixture": synthetic,
            "registered_at": now_iso(),
            "media": media,
        }
    )
    registry.assets.append(record)
    write_yaml(ws.path("assets/registry.yaml"), registry.model_dump(mode="json"))
    return record
