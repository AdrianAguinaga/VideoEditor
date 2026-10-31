"""FFmpeg/ffprobe infrastructure: argv-only subprocesses (never a shell), logged stderr, normalized probe."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from .contracts import MediaInfo
from .util import NotConfigured, ToolError, ValidationFailed

_IMAGE_FORMATS = ("image2", "png_pipe", "jpeg_pipe", "webp_pipe", "bmp_pipe", "tiff_pipe")


def tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise NotConfigured(f"{name} not found on PATH", hint="install FFmpeg (see docs/setup.md)")
    return path


def system_font() -> Path | None:
    """A sans font every OS ships. drawtext needs a file: FFmpeg's Fontconfig often has no config on Windows."""
    windows = Path(os.environ.get("WINDIR", "C:/Windows"), "Fonts")
    for path in [
        windows / "arial.ttf",
        windows / "segoeui.ttf",
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/dejavu/DejaVuSans.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
    ]:
        if path.is_file():
            return path
    return None


def run_tool(
    argv: list[str], *, log: Path | None = None, cwd: Path | None = None, timeout: float | None = None
) -> subprocess.CompletedProcess[str]:
    try:
        proc = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=cwd,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        raise ToolError(f"{Path(argv[0]).stem} timed out after {timeout}s") from None
    if log is not None:
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a", encoding="utf-8") as fh:
            fh.write(f"$ {' '.join(argv)}\n[exit {proc.returncode}]\n{proc.stderr}\n")
    if proc.returncode != 0:
        tail = "\n".join(proc.stderr.strip().splitlines()[-8:])
        raise ToolError(f"{Path(argv[0]).stem} failed (exit {proc.returncode}):\n{tail}")
    return proc


def tool_version(name: str) -> str:
    out = run_tool([tool(name), "-hide_banner", "-version"]).stdout
    return out.splitlines()[0] if out else "unknown"


def probe(path: Path) -> MediaInfo:
    try:
        out = run_tool(
            [
                tool("ffprobe"),
                "-v",
                "error",
                "-print_format",
                "json",
                "-show_format",
                "-show_streams",
                str(path),
            ],
            timeout=120,
        ).stdout
    except ToolError as exc:
        raise ValidationFailed(f"not a decodable media file: {path.name}", hint=str(exc)) from None
    data = json.loads(out)
    streams = data.get("streams", [])
    fmt = data.get("format", {})
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    format_name = fmt.get("format_name", "")
    is_image = video is not None and audio is None and format_name in _IMAGE_FORMATS
    if video is None and audio is None:
        raise ValidationFailed(f"no audio or video streams in {path.name}")
    duration = fmt.get("duration")
    fps = None
    if video and not is_image and video.get("avg_frame_rate", "0/0") != "0/0":
        num, den = video["avg_frame_rate"].split("/")
        fps = round(int(num) / int(den), 3) if int(den) else None
    return MediaInfo(
        kind="image" if is_image else ("video" if video else "audio"),
        format_name=format_name,
        duration_ms=None if is_image or duration is None else round(float(duration) * 1000),
        has_video=video is not None and not is_image,
        has_audio=audio is not None,
        width=video.get("width") if video else None,
        height=video.get("height") if video else None,
        fps=fps,
        sample_rate=int(audio["sample_rate"]) if audio and "sample_rate" in audio else None,
        channels=audio.get("channels") if audio else None,
        codecs=[s.get("codec_name", "?") for s in streams],
    )


def decode_errors(path: Path, log: Path | None = None) -> str | None:
    """Full decode pass; returns the error text or None when the file decodes cleanly."""
    try:
        proc = run_tool([tool("ffmpeg"), "-nostdin", "-v", "error", "-i", str(path), "-f", "null", "-"], log=log)
    except ToolError as exc:
        return str(exc)
    return proc.stderr.strip() or None


def max_volume_db(path: Path) -> float | None:
    proc = run_tool(
        [
            tool("ffmpeg"),
            "-nostdin",
            "-hide_banner",
            "-i",
            str(path),
            "-map",
            "0:a:0",
            "-af",
            "volumedetect",
            "-f",
            "null",
            "-",
        ]
    )
    for line in proc.stderr.splitlines():
        if "max_volume:" in line:
            return float(line.split("max_volume:")[1].split("dB")[0])
    return None
