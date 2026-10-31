"""Technical QA. It checks decodability, streams, geometry, duration and subtitles.

It never decides editorial acceptance: that is a human approval (see runs.approve).
"""

from __future__ import annotations

import re
from pathlib import Path

from .contracts import QaCheck
from .media import decode_errors, max_volume_db, probe
from .util import ValidationFailed

SILENCE_DB = -60.0
_SRT_TIME = re.compile(r"(\d+):(\d\d):(\d\d)[,.](\d{3}) --> (\d+):(\d\d):(\d\d)[,.](\d{3})")


def check_video(
    path: Path,
    *,
    expected_ms: int | None,
    width: int | None,
    height: int | None,
    tolerance_ms: int,
    log: Path | None = None,
) -> list[QaCheck]:
    if not path.is_file():
        return [QaCheck(name="exists", status="failed", detail=f"missing {path.name}")]
    errors = decode_errors(path, log)
    checks = [QaCheck(name="decodes", status="failed" if errors else "passed", detail=(errors or "")[:500])]
    try:
        info = probe(path)
    except ValidationFailed as exc:
        return [*checks, QaCheck(name="probe", status="failed", detail=str(exc))]
    checks.append(
        QaCheck(
            name="streams",
            status="passed" if info.has_video and info.has_audio else "failed",
            detail=f"video={info.has_video} audio={info.has_audio}",
        )
    )
    if height:
        ok = info.height == height and (width is None or info.width == width)
        checks.append(
            QaCheck(
                name="resolution",
                status="passed" if ok else "failed",
                detail=f"{info.width}x{info.height}, expected {width or 'any'}x{height}",
            )
        )
    if expected_ms is not None:
        actual = info.duration_ms or 0
        ok = abs(actual - expected_ms) <= tolerance_ms
        checks.append(
            QaCheck(
                name="duration",
                status="passed" if ok else "failed",
                detail=f"{actual} ms, expected {expected_ms} ± {tolerance_ms} ms",
            )
        )
    if info.has_audio:
        peak = max_volume_db(path)
        ok = peak is not None and peak > SILENCE_DB
        checks.append(
            QaCheck(
                name="audio_not_silent",
                status="passed" if ok else "failed",
                detail=f"max_volume {peak} dB (threshold {SILENCE_DB} dB)",
            )
        )
    return checks


def parse_srt_times(text: str) -> list[tuple[int, int]]:
    def ms(h: str, m: str, s: str, f: str) -> int:
        return ((int(h) * 60 + int(m)) * 60 + int(s)) * 1000 + int(f)

    return [(ms(*m.groups()[:4]), ms(*m.groups()[4:])) for m in _SRT_TIME.finditer(text)]


def check_subtitles(path: Path, duration_ms: int | None) -> QaCheck:
    if not path.is_file():
        return QaCheck(name="subtitles", status="failed", detail=f"missing {path.name}")
    times = parse_srt_times(path.read_text("utf-8"))
    problems = []
    for i, (start, end) in enumerate(times):
        if end <= start:
            problems.append(f"cue {i + 1} has end <= start")
        if i and start < times[i - 1][1]:
            problems.append(f"cue {i + 1} overlaps the previous one")
        if duration_ms is not None and end > duration_ms:
            problems.append(f"cue {i + 1} ends after the video ({end} > {duration_ms} ms)")
    return QaCheck(
        name="subtitles",
        status="failed" if problems else "passed",
        detail="; ".join(problems[:5]) or f"{len(times)} cues within bounds",
    )
