"""doctor / bootstrap-check / schema export. Read-only unless a function says otherwise."""

from __future__ import annotations

import json
import platform
import shutil
from dataclasses import asdict, dataclass
from importlib import metadata
from pathlib import Path

from .contracts import SCHEMAS, AsrSettings
from .media import run_tool
from .transcribe import ALIGNER_STATUS, model_entry, model_ready
from .util import PipelineError, load_yaml
from .workspace import Workspace


@dataclass
class Check:
    component: str
    required: bool
    installed: bool
    detectable: bool
    configured: bool
    tested: bool
    detail: str = ""

    @property
    def state(self) -> str:
        if self.tested:
            return "tested"
        if self.configured:
            return "configured"
        if self.detectable:
            return "detectable"
        return "installed" if self.installed else "missing"


def _read_state(ws: Workspace | None, name: str) -> dict:
    if ws is None:
        return {}
    path = ws.root / ".local/state" / name
    return json.loads(path.read_text("utf-8")) if path.is_file() else {}


def doctor(ws: Workspace | None) -> list[Check]:
    checks = [Check("python", True, True, True, True, True, platform.python_version())]
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        encoders = run_tool([ffmpeg, "-hide_banner", "-encoders"]).stdout
        filters = run_tool([ffmpeg, "-hide_banner", "-filters"]).stdout
        version = run_tool([ffmpeg, "-hide_banner", "-version"]).stdout.splitlines()[0]
        missing = [
            n
            for n, text in (
                ("libx264", encoders),
                ("aac", encoders),
                ("subtitles", filters),
                ("concat", filters),
            )
            if f" {n} " not in text
        ]
        verified = _read_state(ws, "render-verified.json")
        checks.append(
            Check(
                "ffmpeg",
                True,
                True,
                True,
                not missing,
                bool(verified) and not missing,
                f"{version}; missing: {missing or 'none'}; last verified render: {verified.get('run')}",
            )
        )
    else:
        checks.append(Check("ffmpeg", True, False, False, False, False, "not on PATH"))
    ffprobe = shutil.which("ffprobe")
    rendered = bool(_read_state(ws, "render-verified.json"))  # a verified render probed its output
    checks.append(
        Check(
            "ffprobe",
            True,
            bool(ffprobe),
            bool(ffprobe),
            bool(ffprobe),
            bool(ffprobe) and rendered,
            ffprobe or "not on PATH",
        )
    )
    try:
        fw_version = metadata.version("faster-whisper")
        ct2_version = metadata.version("ctranslate2")
    except metadata.PackageNotFoundError:
        fw_version = ct2_version = ""
    asr = AsrSettings.model_validate(ws.config.defaults.get("asr", {}) if ws else {})
    configured = detail = ""
    if ws and fw_version:
        try:
            entry = model_entry(ws, asr.model)
            configured = "yes" if model_ready(ws, asr.model) else ""
            detail = f"model {asr.model} ({entry['repo_id']}@{entry['revision'][:8]}) " + (
                "downloaded" if configured else "NOT downloaded: run `video-pipeline models fetch`"
            )
        except PipelineError as exc:
            detail = str(exc)
        verified = _read_state(ws, "asr-verified.json")
        tested = bool(configured) and verified.get("model") == asr.model
        detail += f"; device={asr.device}/{asr.compute_type}; verified on real speech: {verified.get('at', 'never')}"
    else:
        tested = False
    checks.append(
        Check(
            "asr:faster-whisper",
            True,
            bool(fw_version),
            bool(fw_version),
            bool(configured),
            tested,
            f"faster-whisper {fw_version or 'missing'}, ctranslate2 {ct2_version or 'missing'}; {detail}",
        )
    )
    checks.append(Check("aligner", False, False, False, False, False, ALIGNER_STATUS))
    checks.append(
        Check(
            "workspace",
            True,
            ws is not None,
            ws is not None,
            ws is not None and not schema_drift(ws),
            False,
            str(ws.root) if ws else "not initialized: run `video-pipeline init`",
        )
    )
    return checks


def doctor_json(checks: list[Check]) -> str:
    return json.dumps([asdict(c) | {"state": c.state} for c in checks], indent=1)


def schema_documents() -> dict[str, str]:
    return {
        name: json.dumps(model.model_json_schema(), indent=1, ensure_ascii=False) + "\n"
        for name, model in SCHEMAS.items()
    }


def export_schemas(ws: Workspace) -> list[Path]:
    written = []
    for name, text in schema_documents().items():
        path = ws.root / "config/schemas" / f"{name}.schema.json"
        if not path.is_file() or path.read_text("utf-8") != text:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, "utf-8")
            written.append(path)
    return written


def schema_drift(ws: Workspace) -> list[str]:
    drift = []
    for name, text in schema_documents().items():
        path = ws.root / "config/schemas" / f"{name}.schema.json"
        if not path.is_file() or path.read_text("utf-8") != text:
            drift.append(name)
    return drift


def bootstrap_pending(root: Path) -> list[str]:
    """Pending bootstrap actions. Read-only: never installs, downloads or rewrites anything."""
    pending = []
    if not (root / "uv.lock").is_file():
        pending.append("uv.lock missing: run `uv lock` (then `uv sync --locked`)")
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        pending.append("FFmpeg/ffprobe missing from PATH (see docs/setup.md)")
    try:
        ws = Workspace(root)
    except PipelineError:
        return [*pending, "workspace not initialized: run `video-pipeline init`"]
    for profile in sorted((root / "config/profiles").glob("*.yaml")):
        try:
            ws.profile(profile.stem)
        except PipelineError as exc:
            pending.append(f"invalid profile {profile.name}: {exc}")
    if drift := schema_drift(ws):
        pending.append(f"schemas out of date ({', '.join(drift)}): run `video-pipeline schemas export`")
    models = (load_yaml(root / "config/models.yaml") or {}).get("models", {})
    for name, entry in models.items():
        if entry.get("approved") and not model_ready(ws, name):
            pending.append(f"approved model {name} not downloaded: run `video-pipeline models fetch {name}`")
    return pending
