"""Real Spanish ASR with the installed backend and downloaded weights. No mocks.

Needs an authorized voice sample:  VIDEO_PIPELINE_ASR_SAMPLE=<path>  (optional:
VIDEO_PIPELINE_ASR_EXPECT="palabra1,palabra2" for words that must appear). Without it the test is SKIPPED,
which means real ASR is NOT verified.
"""

from __future__ import annotations

import json
import os
import unicodedata
from pathlib import Path

import pytest

from tests.conftest import PROJECT, cli
from video_pipeline.transcribe import model_ready
from video_pipeline.workspace import Workspace

pytestmark = [pytest.mark.integration, pytest.mark.asr]


def _plain(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()


def test_real_spanish_transcription(ws: Workspace, monkeypatch: pytest.MonkeyPatch) -> None:
    sample = os.environ.get("VIDEO_PIPELINE_ASR_SAMPLE")
    if not sample or not Path(sample).is_file():
        pytest.skip("no authorized Spanish sample (set VIDEO_PIPELINE_ASR_SAMPLE): real ASR NOT verified")
    models = PROJECT / ".local/models"
    monkeypatch.setenv("VIDEO_PIPELINE_MODELS_DIR", str(models))
    if not model_ready(ws, "faster-whisper-medium"):
        pytest.skip("faster-whisper-medium weights not downloaded: real ASR NOT verified")

    root = ws.root
    assert cli(root, "series", "create", "asr-check", "--title", "ASR").returncode == 0
    assert cli(root, "video", "create", "asr-check", "muestra", "--title", "Muestra").returncode == 0
    assert cli(root, "ingest", "asr-check/muestra", sample, "--id", "voz").returncode == 0
    result = cli(root, "transcribe", "asr-check/muestra", "voz")
    assert result.returncode == 0, result.stderr
    out = Path(result.stdout.split("transcript:")[1].strip())
    data = json.loads(out.read_text("utf-8"))

    assert data["backend"]["name"] == "faster-whisper"
    assert data["backend"]["revision"]
    assert data["language"] == "es"
    text = " ".join(s["text"] for s in data["segments"])
    assert len(text.split()) >= 3, f"almost no speech recognized: {text!r}"
    for seg in data["segments"]:
        assert 0 <= seg["start_ms"] < seg["end_ms"] <= data["duration_ms"] + 500
    for word in filter(None, os.environ.get("VIDEO_PIPELINE_ASR_EXPECT", "").split(",")):
        assert _plain(word.strip()) in _plain(text), f"expected {word!r} in {text!r}"
