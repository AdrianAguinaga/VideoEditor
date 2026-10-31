import json
import os
import socket
from pathlib import Path

import pytest

from video_pipeline import diagnostics, runs
from video_pipeline.contracts import RunRecord
from video_pipeline.util import LockedError, UsageError, load_yaml, write_yaml
from video_pipeline.workspace import Workspace, init_workspace, lock_state, unlock, video_lock


def _three_videos(ws: Workspace) -> None:
    ws.create_series("curso-contabilidad", "Curso de Contabilidad")
    ws.create_video("curso-contabilidad", "introduccion", "Introducción al curso")
    ws.create_video("curso-contabilidad", "clase-001", "Clase 1: El balance")
    ws.create_video("curso-contabilidad", "clase-002", "Clase 2: Cuentas")


def test_series_order_and_no_duplicates(ws: Workspace) -> None:
    _three_videos(ws)
    assert ws.load_series("curso-contabilidad").videos == ["introduccion", "clase-001", "clase-002"]
    with pytest.raises(UsageError):
        ws.create_video("curso-contabilidad", "clase-001", "otra")
    with pytest.raises(UsageError):
        ws.create_series("curso-contabilidad", "otra")


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("curso-contabilidad/clase-002", "curso-contabilidad/clase-002"),
        ("clase 1", "curso-contabilidad/clase-001"),
        ("Clase 001 contabilidad", "curso-contabilidad/clase-001"),
        ("introducción", "curso-contabilidad/introduccion"),
        ("balance", "curso-contabilidad/clase-001"),
    ],
)
def test_resolve_natural_names(ws: Workspace, query: str, expected: str) -> None:
    _three_videos(ws)
    assert ws.resolve(query).key == expected


def test_resolve_ambiguous_and_missing(ws: Workspace) -> None:
    _three_videos(ws)
    with pytest.raises(UsageError, match="ambiguous"):
        ws.resolve("clase")
    with pytest.raises(UsageError, match="no video"):
        ws.resolve("clase 9")


def test_settings_precedence(ws: Workspace) -> None:
    _three_videos(ws)
    cfg = load_yaml(ws.root / "config/workspace.yaml")
    cfg["defaults"] = {"profile": "720p30", "asr": {"beam_size": 3, "language": "es"}}
    write_yaml(ws.root / "config/workspace.yaml", cfg)
    ws = Workspace(ws.root)
    series = load_yaml(ws.series_dir("curso-contabilidad") / "series.yaml")
    series["defaults"] = {"style": {"intro": {"id": "cortinilla-entrada", "version": 1}}, "asr": {"beam_size": 4}}
    write_yaml(ws.series_dir("curso-contabilidad") / "series.yaml", series)
    ref = ws.resolve("curso-contabilidad/clase-002")
    video = load_yaml(ref.dir / "video.yaml")
    video["overrides"] = {"style": {"intro": None}}  # this class has no intro
    write_yaml(ref.dir / "video.yaml", video)

    s = ws.settings(ref, override={"asr": {"beam_size": 1}})
    assert s.profile == "720p30"  # workspace
    assert s.asr.language == "es"
    assert s.asr.beam_size == 1  # run override beats series (4) and workspace (3)
    assert s.style.intro is None  # video beats series
    assert ws.settings(ws.resolve("clase 1")).style.intro is not None  # sibling still inherits
    assert ws.settings(ws.resolve("clase 1")).asr.beam_size == 4


def test_init_is_idempotent(tmp_path: Path) -> None:
    root = tmp_path / "w"
    assert init_workspace(root, "w")
    (root / "config/workspace.yaml").write_text("schema_version: 1\nname: edited by user\n", "utf-8")
    assert init_workspace(root, "w") == []
    assert "edited by user" in (root / "config/workspace.yaml").read_text("utf-8")


def test_lock_held_stale_and_unlock(ws: Workspace) -> None:
    _three_videos(ws)
    ref = ws.resolve("clase 1")
    with video_lock(ref, "test"):
        assert lock_state(ref)[0] == "held"
        with pytest.raises(LockedError, match="another writer"), video_lock(ref, "second"):
            pass
        with pytest.raises(LockedError):
            unlock(ref)  # never removes a live owner's lock
    assert lock_state(ref)[0] == "free"
    dead_pid = 2**22 + 12345  # not a running process
    (ref.dir / ".lock").write_text(json.dumps({"pid": dead_pid, "host": socket.gethostname()}), "utf-8")
    assert lock_state(ref)[0] == "stale"
    with pytest.raises(LockedError, match="stale"), video_lock(ref, "x"):
        pass
    assert unlock(ref)["pid"] == dead_pid
    assert lock_state(ref)[0] == "free"


def test_interrupted_run_is_detected(ws: Workspace) -> None:
    _three_videos(ws)
    ref = ws.resolve("clase 1")
    run_id, run_dir = runs.create_run_dir(ref, "preview")
    runs.save_run(
        run_dir,
        RunRecord(
            id=run_id,
            video=ref.key,
            mode="preview",
            status="running",
            started_at="t",
            timeline="editorial/timelines/v1.yaml",
            timeline_sha256="0" * 64,
        ),
    )
    assert [s for _, s in runs.list_runs(ref)] == ["interrupted"]
    second_id, _ = runs.create_run_dir(ref, "preview")
    assert second_id != run_id  # a new run never reuses a directory


def test_doctor_reports_not_configured(ws: Workspace, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VIDEO_PIPELINE_MODELS_DIR", str(ws.root / "no-models-here"))
    checks = {c.component: c for c in diagnostics.doctor(ws)}
    assert checks["asr:faster-whisper"].installed
    assert not checks["asr:faster-whisper"].configured
    assert not checks["asr:faster-whisper"].tested
    assert checks["aligner"].detail == "not_configured" and checks["aligner"].state == "missing"
    pending = diagnostics.bootstrap_pending(ws.root)
    assert any("not downloaded" in p for p in pending)


def test_pid_alive_for_current_process() -> None:
    from video_pipeline.workspace import pid_alive

    assert pid_alive(os.getpid())
