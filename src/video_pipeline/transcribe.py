"""ASR application service. Backend: faster-whisper (local, CPU int8 on this machine).

Alignment (WhisperX or similar) is a separate, optional capability and is NOT configured.
"""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol

from .contracts import AsrSettings, BackendInfo, Segment, Transcript, Word
from .media import tool
from .util import NotConfigured, ToolError, UsageError, ValidationFailed, check_id, load_yaml, now_iso, sha256_file
from .workspace import VideoRef, Workspace, video_lock

ALIGNER_STATUS = "not_configured"
LIMITATIONS = [
    "word timestamps come from Whisper cross-attention, not forced alignment; expect ~100-300 ms error",
    "raw ASR output: names, figures and technical terms must be reviewed against the glossary",
]


class Transcriber(Protocol):
    def transcribe(self, media: Path, language: str) -> tuple[list[Segment], dict[str, Any]]: ...


def model_entry(ws: Workspace, name: str) -> dict[str, Any]:
    models = (load_yaml(ws.path("config/models.yaml")) or {}).get("models", {})
    if name not in models:
        raise NotConfigured(f"ASR model {name!r} is not declared in config/models.yaml")
    entry: dict[str, Any] = models[name]
    return entry


def model_dir(ws: Workspace, name: str) -> Path:
    shared = os.environ.get("VIDEO_PIPELINE_MODELS_DIR")  # optional cache shared between workspaces
    return Path(shared).resolve() / check_id(name, "model name") if shared else ws.path(".local/models", name)


def model_ready(ws: Workspace, name: str) -> bool:
    return (model_dir(ws, name) / "model.bin").is_file()


def fetch_model(ws: Workspace, name: str) -> Path:
    """Download pinned weights if missing (idempotent)."""
    entry = model_entry(ws, name)
    target = model_dir(ws, name)
    if model_ready(ws, name):
        return target
    from huggingface_hub import snapshot_download

    snapshot_download(entry["repo_id"], revision=entry["revision"], local_dir=str(target))
    return target


def _decode_audio(media: Path) -> Any:
    """16 kHz mono float32 PCM via FFmpeg: faster-whisper 1.2.1's own PyAV decoder breaks on PyAV >= 15."""
    import numpy as np

    argv = [
        tool("ffmpeg"),
        "-v",
        "error",
        "-nostdin",
        "-i",
        str(media),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-f",
        "f32le",
        "-",
    ]
    proc = subprocess.run(argv, capture_output=True, check=False)
    if proc.returncode != 0:
        raise ToolError(
            f"ffmpeg could not decode {media.name}: {proc.stderr.decode('utf-8', 'replace').strip()[-500:]}"
        )
    return np.frombuffer(proc.stdout, dtype=np.float32)


class FasterWhisperTranscriber:
    def __init__(self, ws: Workspace, settings: AsrSettings) -> None:
        if not model_ready(ws, settings.model):
            raise NotConfigured(
                f"ASR model {settings.model!r} is not downloaded",
                hint=f"run `video-pipeline models fetch {settings.model}`",
            )
        try:
            import faster_whisper
            from faster_whisper import WhisperModel
        except ImportError:
            raise NotConfigured("faster-whisper is not installed", hint="run `uv sync`") from None
        self.settings = settings
        entry = model_entry(ws, settings.model)
        self.info = BackendInfo(
            name="faster-whisper",
            version=faster_whisper.__version__,
            model=entry["repo_id"],
            revision=entry.get("revision"),
            device=settings.device,
            compute_type=settings.compute_type,
        )
        self.model = WhisperModel(
            str(model_dir(ws, settings.model)), device=settings.device, compute_type=settings.compute_type
        )

    def transcribe(self, media: Path, language: str) -> tuple[list[Segment], dict[str, Any]]:
        try:
            segments_iter, info = self.model.transcribe(
                _decode_audio(media),
                language=language,
                beam_size=self.settings.beam_size,
                vad_filter=self.settings.vad_filter,
                word_timestamps=self.settings.word_timestamps,
            )
            segments = [
                Segment(
                    id=i,
                    start_ms=round(s.start * 1000),
                    end_ms=round(s.end * 1000),
                    text=s.text.strip(),
                    words=[
                        Word(
                            start_ms=round(w.start * 1000),
                            end_ms=round(w.end * 1000),
                            text=w.word.strip(),
                            probability=round(w.probability, 3),
                        )
                        for w in (s.words or [])
                    ],
                )
                for i, s in enumerate(segments_iter)
            ]
        except Exception as exc:  # backend errors are surfaced, never swallowed
            raise ToolError(f"faster-whisper failed on {media.name}: {exc}") from exc
        return segments, {
            "language_probability": round(info.language_probability, 3),
            "duration_ms": round(info.duration * 1000),
        }


def transcribe_input(
    ws: Workspace,
    ref: VideoRef,
    input_id: str,
    transcriber: Transcriber | None = None,
    settings: AsrSettings | None = None,
) -> Path:
    settings = settings or ws.settings(ref).asr
    record = next((i for i in ws.inventory(ref).inputs if i.id == input_id), None)
    if record is None:
        raise UsageError(f"input {input_id!r} not found in {ref.key}")
    if not record.media.has_audio:
        raise ValidationFailed(f"input {input_id!r} has no audio stream")
    media_path = ref.dir / record.path
    if sha256_file(media_path) != record.sha256:
        raise ValidationFailed(f"input {input_id!r} no longer matches its ingested hash")
    backend = transcriber or FasterWhisperTranscriber(ws, settings)
    segments, extra = backend.transcribe(media_path, settings.language)
    info = getattr(backend, "info", None) or BackendInfo(
        name=type(backend).__name__,
        version="test",
        model="n/a",
        revision=None,
        device="n/a",
        compute_type="n/a",
    )
    transcript = Transcript(
        video=ref.key,
        input_id=input_id,
        input_sha256=record.sha256,
        language=settings.language,
        language_probability=extra.get("language_probability"),
        duration_ms=extra.get("duration_ms", record.media.duration_ms or 0),
        created_at=now_iso(),
        backend=info,
        segments=segments,
        limitations=LIMITATIONS,
    )
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    out = ref.dir / "editorial/transcript" / f"{input_id}.{stamp}.asr.json"
    with video_lock(ref, "transcribe"), out.open("x", encoding="utf-8") as fh:  # raw ASR: never overwrite
        json.dump(transcript.model_dump(mode="json"), fh, ensure_ascii=False, indent=1)
    if segments and isinstance(backend, FasterWhisperTranscriber):
        _mark_verified(ws, settings.model, info, record.sha256, len(segments))
    return out


def _mark_verified(ws: Workspace, model: str, info: BackendInfo, input_sha: str, n: int) -> None:
    state = ws.path(".local/state/asr-verified.json")
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(
        json.dumps(
            {
                "model": model,
                "revision": info.revision,
                "backend": info.version,
                "input_sha256": input_sha,
                "segments": n,
                "at": now_iso(),
            }
        ),
        "utf-8",
    )
