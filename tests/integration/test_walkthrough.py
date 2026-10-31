"""End-to-end with real FFmpeg/ffprobe and the real CLI (subprocess, real exit codes). No mocks."""

from __future__ import annotations

import json
import os
import socket
import stat
from pathlib import Path

import pytest

from tests.conftest import cli
from video_pipeline import fixtures
from video_pipeline.util import load_yaml, sha256_file, write_yaml
from video_pipeline.workspace import Workspace

pytestmark = pytest.mark.integration
SERIES = "curso-contabilidad"
VIDEOS = {"introduccion": "Introducción", "clase-001": "Clase 1: El balance", "clase-002": "Clase 2: Cuentas"}


def ok(result):  # noqa: ANN001, ANN201
    assert result.returncode == 0, f"exit {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    return result


def run_id_of(result) -> str:  # noqa: ANN001
    return result.stdout.split()[1].rstrip(":")


@pytest.fixture
def series(ws: Workspace, media: dict[str, Path]) -> Workspace:
    root = ws.root
    ok(cli(root, "series", "create", SERIES, "--title", "Curso de Contabilidad"))
    for vid, title in VIDEOS.items():
        ok(cli(root, "video", "create", SERIES, vid, "--title", title))
    ok(
        cli(
            root,
            "asset",
            "add",
            media["cortinilla"],
            "--id",
            "cortinilla-entrada",
            "--version",
            "1",
            "--kind",
            "cortinilla",
            "--role",
            "entrada",
            "--license",
            "synthetic fixture",
            "--permissions",
            "tests only",
            "--synthetic",
        )
    )
    data = load_yaml(root / f"series/{SERIES}/series.yaml")
    data["defaults"] = {"profile": "720p30", "style": {"intro": {"id": "cortinilla-entrada", "version": 1}}}
    write_yaml(root / f"series/{SERIES}/series.yaml", data)
    return ws


def ingest_and_preview(root: Path, video: str, src: Path, timeline: str = "v1") -> str:
    ok(cli(root, "ingest", f"{SERIES}/{video}", src, "--id", "grabacion"))
    ok(cli(root, "timeline", "scaffold", f"{SERIES}/{video}", timeline, "--source", "grabacion"))
    return run_id_of(ok(cli(root, "preview", f"{SERIES}/{video}", timeline)))


def test_three_videos_isolated_and_originals_untouched(series: Workspace, media: dict[str, Path]) -> None:
    root = series.root
    before = {k: sha256_file(p) for k, p in media.items()}
    runs = {vid: ingest_and_preview(root, vid, media["clase"]) for vid in ("introduccion", "clase-001")}
    runs["clase-002"] = ingest_and_preview(root, "clase-002", media["voz"])  # different source
    assert {k: sha256_file(p) for k, p in media.items()} == before  # sources never modified

    for vid, run_id in runs.items():
        vdir = root / f"series/{SERIES}/videos/{vid}"
        run = load_yaml(vdir / f"runs/{run_id}/run.yaml")
        inventory = load_yaml(vdir / "manifests/inputs.yaml")
        own = {i["id"]: i["sha256"] for i in inventory["inputs"]}
        assert run["inputs"] == own  # a run only references its own video's inputs
        assert run["video"] == f"{SERIES}/{vid}"
        assert run["assets"] == {"cortinilla-entrada@1": sha256_file(media["cortinilla"])}  # inherited intro
        copy = vdir / inventory["inputs"][0]["path"]
        assert not os.stat(copy).st_mode & stat.S_IWRITE  # ingested copy is read-only
        outputs = list((vdir / f"runs/{run_id}/outputs").rglob("*.mp4"))
        assert len(outputs) == 1 and outputs[0].is_relative_to(vdir)
    # 2 s cortinilla + 6 s source
    for vid, run_id in runs.items():
        run = load_yaml(root / f"series/{SERIES}/videos/{vid}/runs/{run_id}/run.yaml")
        assert run["expected_duration_ms"] == 8000 and run["status"] == "succeeded"


def test_cut_cortinilla_subtitles_approval_master(series: Workspace, media: dict[str, Path]) -> None:
    root = series.root
    video = f"{SERIES}/clase-001"
    vdir = root / f"series/{SERIES}/videos/clase-001"
    ok(cli(root, "ingest", "clase 1", media["clase"], "--id", "grabacion"))
    sha = load_yaml(vdir / "manifests/inputs.yaml")["inputs"][0]["sha256"]
    transcript = {
        "schema_version": 1,
        "video": video,
        "input_id": "grabacion",
        "input_sha256": sha,
        "language": "es",
        "duration_ms": 6000,
        "created_at": "t",
        "limitations": ["handcrafted fixture, not ASR"],
        "backend": {
            "name": "handcrafted-fixture",
            "version": "0",
            "model": "none",
            "revision": None,
            "device": "n/a",
            "compute_type": "n/a",
        },
        "segments": [
            {
                "id": 0,
                "start_ms": 100,
                "end_ms": 1900,
                "text": "Hola a todos.",
                "words": [
                    {"start_ms": 100, "end_ms": 900, "text": "Hola"},
                    {"start_ms": 900, "end_ms": 1900, "text": "a todos."},
                ],
            },
            {"id": 1, "start_ms": 2100, "end_ms": 2900, "text": "eh perdón", "words": []},
            {"id": 2, "start_ms": 3200, "end_ms": 5800, "text": "No son 300 pesos.", "words": []},
        ],
    }
    (vdir / "editorial/transcript/grabacion.fixture.asr.json").write_text(json.dumps(transcript), "utf-8")
    timeline = {
        "schema_version": 1,
        "video": video,
        "transcripts": ["editorial/transcript/grabacion.fixture.asr.json"],
        "clips": [
            {"kind": "asset", "asset": "cortinilla-entrada", "version": 1},
            {"kind": "source", "input": "grabacion", "in_ms": 0, "out_ms": 2000},
            {"kind": "source", "input": "grabacion", "in_ms": 3000, "out_ms": 6000},
        ],
        "cuts": [{"input": "grabacion", "start_ms": 2000, "end_ms": 3000, "reason": "muletilla", "status": "proposed"}],
    }
    write_yaml(vdir / "editorial/timelines/v1.yaml", timeline)

    review = ok(cli(root, "timeline", "review", "clase 1", "v1")).stdout
    assert "muletilla" in review and "eh perdón" in review and "proposed" in review
    assert cli(root, "timeline", "validate", "clase 1", "v1", "--mode", "master").returncode == 5  # proposed cut

    preview = ok(cli(root, "preview", "clase 1", "v1"))
    run_id = run_id_of(preview)
    srt = (vdir / f"runs/{run_id}/outputs/subtitles/{SERIES}_clase-001.srt").read_text("utf-8")
    assert "00:00:02,100 --> 00:00:03,900\nHola a todos." in srt  # +2 s cortinilla
    assert "perdón" not in srt  # cut text removed
    assert "00:00:04,200 --> 00:00:06,800\nNo son 300 pesos." in srt  # +2 s intro, -1 s cut

    assert cli(root, "render", "clase 1", "v1").returncode == 5  # no approval yet
    ok(cli(root, "approve", "clase 1", run_id, "--actor", "tester"))
    timeline["cuts"][0]["status"] = "accepted"  # editing the timeline invalidates the approval
    write_yaml(vdir / "editorial/timelines/v1.yaml", timeline)
    result = cli(root, "render", "clase 1", "v1")
    assert result.returncode == 5 and "approval" in result.stderr
    run2 = run_id_of(ok(cli(root, "preview", "clase 1", "v1")))
    ok(cli(root, "approve", "clase 1", run2, "--actor", "tester"))
    master = ok(cli(root, "render", "clase 1", "v1"))
    assert "[PASS] duration: 7000 ms" in master.stdout or "[PASS] duration" in master.stdout
    master_id = run_id_of(master)
    delivery = vdir / f"runs/{master_id}/outputs/delivery"
    assert sorted(p.name for p in delivery.iterdir()) == [f"{SERIES}_clase-001.{e}" for e in ("mp4", "srt", "vtt")]
    assert load_yaml(vdir / f"runs/{master_id}/run.yaml")["approval"].endswith(run2)

    # previous runs are untouched by later ones
    first_preview = vdir / f"runs/{run_id}/outputs/previews/{SERIES}_clase-001_preview.mp4"
    recorded = load_yaml(vdir / f"runs/{run_id}/run.yaml")["artifacts"][-1]
    assert sha256_file(first_preview) == recorded["sha256"]

    # QA catches a deliberately damaged deliverable
    ok(cli(root, "qa", "clase 1", master_id))
    master_file = vdir / f"runs/{master_id}/outputs/masters/{SERIES}_clase-001.mp4"
    data = master_file.read_bytes()
    master_file.write_bytes(data[: len(data) // 3])
    damaged = cli(root, "qa", "clase 1", master_id)
    assert damaged.returncode == 1
    assert "[FAIL] integrity" in damaged.stdout and "[FAIL] d" in damaged.stdout  # decodes/duration


def test_effects_transitions_overlays_music_and_audio(series: Workspace, media: dict[str, Path]) -> None:
    """Every production layer in one real render: graph, duration (transition overlap), traceability, rejections."""
    root = series.root
    vdir = root / f"series/{SERIES}/videos/clase-001"
    for asset_id, kind, src in [("fondo", "image", "slide"), ("logo-uabc", "logo", "slide"), ("cama", "music", "voz")]:
        ok(
            cli(
                root,
                "asset",
                "add",
                media[src],
                "--id",
                asset_id,
                "--version",
                "1",
                "--kind",
                kind,
                "--license",
                "synthetic fixture",
                "--permissions",
                "tests only",
                "--synthetic",
            )
        )
    ok(cli(root, "ingest", "clase 1", media["clase"], "--id", "grabacion"))
    video = load_yaml(vdir / "video.yaml")
    video["overrides"] = {
        "style": {"background": {"id": "fondo", "version": 1}, "inset_pct": 10},
        "audio": {"highpass_hz": 80, "denoise_db": 12, "compress": True, "loudness_lufs": -16, "edge_fade_ms": 20},
        "color": {"contrast": 1.1, "saturation": 1.2},
    }
    write_yaml(vdir / "video.yaml", video)
    timeline = {
        "schema_version": 1,
        "video": f"{SERIES}/clase-001",
        "clips": [
            {"kind": "asset", "asset": "cortinilla-entrada", "version": 1},
            {"kind": "source", "input": "grabacion", "in_ms": 0, "out_ms": 2000},  # plain join before an xfade
            {
                "kind": "source",
                "input": "grabacion",
                "in_ms": 2000,
                "out_ms": 4000,
                "transition": {"type": "fadeblack"},
            },
            {"kind": "source", "input": "grabacion", "in_ms": 4000, "out_ms": 6000, "transition": {"ms": 500}},
        ],
        "zooms": [
            {"input": "grabacion", "start_ms": 1000, "end_ms": 2000, "x": 0, "y": 0, "w": 640, "h": 360, "reason": "t"}
        ],
        "overlays": [
            {"text": "Dra. Ejemplo\nContabilidad", "input": "grabacion", "start_ms": 500, "end_ms": 2500},
            {"asset": "logo-uabc", "version": 1, "position": "top-right", "size_pct": 10, "opacity": 0.8},
        ],
        "music": [{"asset": "cama", "version": 1, "volume_db": -20}],
        "fade_in_ms": 500,
        "fade_out_ms": 500,
    }
    write_yaml(vdir / "editorial/timelines/v1.yaml", timeline)
    review = ok(cli(root, "timeline", "review", "clase 1", "v1")).stdout
    assert "<- fadeblack 500 ms" in review and "Output duration: 7.00s" in review  # 2 + 2 + 2 + 2 - 0.5 - 0.5

    run_id = run_id_of(ok(cli(root, "preview", "clase 1", "v1")))
    rdir = vdir / f"runs/{run_id}"
    run = load_yaml(rdir / "run.yaml")
    assert run["status"] == "succeeded" and run["expected_duration_ms"] == 7000
    assert set(run["assets"]) == {"cortinilla-entrada@1", "fondo@1", "logo-uabc@1", "cama@1"}
    graph = (rdir / "work/graph.txt").read_text("utf-8")
    for needle in (
        "xfade=transition=fadeblack",
        "acrossfade",
        "drawtext=textfile=overlay-0.txt",
        "sidechaincompress",
        "loudnorm=I=-16",
        "afftdn=nr=12",
        "highpass=f=80",
        "eq=",
        "fade=t=in",
        "colorchannelmixer=aa=0.8",
    ):
        assert needle in graph, needle
    assert (rdir / "work/overlay-0.txt").read_text("utf-8") == "Dra. Ejemplo\nContabilidad"

    bad = {**timeline, "clips": [{**timeline["clips"][0], "transition": {"ms": 500}}, *timeline["clips"][1:]]}
    write_yaml(vdir / "editorial/timelines/v2.yaml", bad)
    result = cli(root, "timeline", "validate", "clase 1", "v2")
    assert result.returncode == 5 and "nothing to transition from" in result.stderr
    bad = {**timeline, "overlays": [{"text": "x", "color": "white:x=0"}]}  # graph injection attempt
    write_yaml(vdir / "editorial/timelines/v3.yaml", bad)
    assert cli(root, "timeline", "validate", "clase 1", "v3").returncode == 5


def test_cortinilla_new_version_does_not_change_history(
    series: Workspace, media: dict[str, Path], tmp_path: Path
) -> None:
    root = series.root
    run1 = ingest_and_preview(root, "clase-001", media["clase"])
    other = tmp_path / "cortinilla-v2.mp4"
    other.write_bytes(media["clase"].read_bytes())  # different content for v2
    assert (
        cli(
            root,
            "asset",
            "add",
            other,
            "--id",
            "cortinilla-entrada",
            "--version",
            "1",
            "--kind",
            "cortinilla",
            "--license",
            "x",
            "--permissions",
            "x",
        ).returncode
        == 2
    )  # id@version is immutable
    ok(
        cli(
            root,
            "asset",
            "add",
            other,
            "--id",
            "cortinilla-entrada",
            "--version",
            "2",
            "--kind",
            "cortinilla",
            "--license",
            "synthetic",
            "--permissions",
            "tests",
            "--synthetic",
        )
    )
    run2 = run_id_of(ok(cli(root, "preview", "clase 1", "v1")))  # timeline still pins v1
    vdir = root / f"series/{SERIES}/videos/clase-001"
    for run_id in (run1, run2):
        assets = load_yaml(vdir / f"runs/{run_id}/run.yaml")["assets"]
        assert assets == {"cortinilla-entrada@1": sha256_file(media["cortinilla"])}


def test_failures_are_reported_with_exit_codes(series: Workspace, media: dict[str, Path], tmp_path: Path) -> None:
    root = series.root
    corrupt = fixtures.corrupt_file(tmp_path / "roto.mp4")
    result = cli(root, "ingest", "clase 1", corrupt)
    assert result.returncode == 5 and "not a decodable media file" in result.stderr
    assert not list((root / f"series/{SERIES}/videos/clase-001/inputs").rglob("*.mp4"))  # nothing copied

    ok(cli(root, "ingest", "clase 1", media["clase"], "--id", "grabacion"))
    assert cli(root, "ingest", "clase 1", media["clase"], "--id", "otra").returncode == 2  # same file twice
    vdir = root / f"series/{SERIES}/videos/clase-001"
    write_yaml(
        vdir / "editorial/timelines/bad.yaml",
        {
            "schema_version": 1,
            "video": f"{SERIES}/clase-001",
            "clips": [
                {"kind": "source", "input": "grabacion", "in_ms": 0, "out_ms": 60_000},
                {"kind": "source", "input": "no-existe", "in_ms": 0, "out_ms": 10},
                {"kind": "asset", "asset": "cortinilla-entrada", "version": 9},
            ],
        },
    )
    result = cli(root, "timeline", "validate", "clase 1", "bad")
    assert result.returncode == 5
    for fragment in ("exceeds", "no-existe", "cortinilla-entrada@9"):
        assert fragment in result.stderr
    assert cli(root, "preview", "clase 1", "bad").returncode == 5
    assert not list((vdir / "runs").iterdir())  # invalid timelines never reach FFmpeg

    result = cli(root, "transcribe", "clase 1", "grabacion")  # this temp workspace has no model weights
    assert result.returncode == 3 and "not downloaded" in result.stderr

    ok(cli(root, "timeline", "scaffold", "clase 1", "v1", "--source", "grabacion"))
    copy = vdir / "inputs/originals/grabacion.mp4"
    os.chmod(copy, stat.S_IWRITE | stat.S_IREAD)
    with copy.open("ab") as fh:
        fh.write(b"tamper")
    result = cli(root, "timeline", "validate", "clase 1", "v1")
    assert result.returncode == 5 and "no longer matches" in result.stderr

    assert cli(root, "resolve", "clase").returncode == 2  # ambiguous natural name


def test_stale_lock_blocks_then_recovers(series: Workspace, media: dict[str, Path]) -> None:
    root = series.root
    ok(cli(root, "ingest", "clase 1", media["clase"], "--id", "grabacion"))
    ok(cli(root, "timeline", "scaffold", "clase 1", "v1", "--source", "grabacion"))
    vdir = root / f"series/{SERIES}/videos/clase-001"
    (vdir / ".lock").write_text(json.dumps({"pid": 2**22 + 777, "host": socket.gethostname()}), "utf-8")
    blocked = cli(root, "preview", "clase 1", "v1")
    assert blocked.returncode == 6 and "stale lock" in blocked.stderr and "unlock" in blocked.stderr
    assert "lock: stale" in ok(cli(root, "status", "clase 1")).stdout
    ok(cli(root, "unlock", "clase 1"))
    ok(cli(root, "preview", "clase 1", "v1"))
    status = ok(cli(root, "status")).stdout
    assert "curso-contabilidad/clase-001" in status and "succeeded" in status
    assert (root / "catalog/views/status.md").is_file()


def test_bootstrap_repeat_changes_nothing(series: Workspace) -> None:
    root = series.root

    def snapshot() -> dict[str, str]:
        return {str(p.relative_to(root)): sha256_file(p) for p in root.rglob("*") if p.is_file()}

    before = snapshot()
    assert "nothing to do" in ok(cli(root, "init")).stdout
    cli(root, "bootstrap-check")  # read-only regardless of result
    assert snapshot() == before
