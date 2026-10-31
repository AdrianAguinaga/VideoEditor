from pathlib import Path

import pytest
from pydantic import ValidationError

from video_pipeline.contracts import AssetRegistry, Cut, SeriesConfig, SourceClip, Timeline, Transcript
from video_pipeline.diagnostics import schema_documents
from video_pipeline.util import ValidationFailed, safe_join, sha256_file

PROJECT = Path(__file__).resolve().parents[2]
SHA = "a" * 64


def test_valid_timeline_example() -> None:
    t = Timeline.model_validate(
        {
            "video": "curso/clase-001",
            "clips": [
                {"kind": "asset", "asset": "cortinilla-entrada", "version": 1},
                {"kind": "source", "input": "grabacion", "in_ms": 0, "out_ms": 1000},
            ],
            "cuts": [{"input": "grabacion", "start_ms": 1000, "end_ms": 1500, "reason": "muletilla"}],
        }
    )
    assert t.cuts[0].status == "proposed"  # detected cuts start as proposals, never approved


@pytest.mark.parametrize(
    "bad",
    [
        {"video": "curso/clase-001", "clips": []},  # empty timeline
        {"video": "Curso/Clase 1", "clips": [{"kind": "source", "input": "a", "in_ms": 0, "out_ms": 1}]},  # bad ids
        {"video": "c/v", "clips": [{"kind": "source", "input": "a", "in_ms": 5, "out_ms": 5}]},  # empty range
        {"video": "c/v", "clips": [{"kind": "source", "input": "a", "in_ms": -1, "out_ms": 5}]},  # negative time
        {"video": "c/v", "clips": [{"kind": "title", "text": "x"}]},  # unknown clip kind
        {"video": "c/v", "clips": [{"kind": "source", "input": "a", "in_ms": 0, "out_ms": 5}], "extra": 1},
    ],
)
def test_timeline_rejections(bad: dict) -> None:
    with pytest.raises(ValidationError):
        Timeline.model_validate(bad)


def test_rejections_other_contracts() -> None:
    with pytest.raises(ValidationError):
        SeriesConfig(id="curso", title="x", videos=["clase-001", "clase-001"])
    with pytest.raises(ValidationError):
        Cut(input="a", start_ms=10, end_ms=10, reason="x")
    with pytest.raises(ValidationError):
        SourceClip(input="../etc", in_ms=0, out_ms=1)
    dup = {
        "id": "c",
        "version": 1,
        "kind": "cortinilla",
        "path": "p",
        "sha256": SHA,
        "license": "x",
        "permissions": "x",
        "registered_at": "t",
    }
    with pytest.raises(ValidationError):
        AssetRegistry.model_validate({"assets": [dup, dup]})
    with pytest.raises(ValidationError):
        Transcript.model_validate(
            {
                "video": "c/v",
                "input_id": "a",
                "input_sha256": "nothex",
                "language": "es",
                "duration_ms": 1,
                "created_at": "t",
                "segments": [],
                "backend": {
                    "name": "x",
                    "version": "1",
                    "model": "m",
                    "revision": None,
                    "device": "cpu",
                    "compute_type": "int8",
                },
            }
        )


def test_committed_schemas_match_code() -> None:
    for name, text in schema_documents().items():
        path = PROJECT / "config/schemas" / f"{name}.schema.json"
        assert path.read_text("utf-8") == text, f"{name} schema drifted: run `video-pipeline schemas export`"


def test_safe_join_rejects_traversal(tmp_path: Path) -> None:
    (tmp_path / "a").mkdir()
    assert safe_join(tmp_path, "a", "b.txt") == (tmp_path / "a" / "b.txt").resolve()
    with pytest.raises(ValidationFailed):
        safe_join(tmp_path, "..", "outside.txt")
    with pytest.raises(ValidationFailed):
        safe_join(tmp_path / "a", tmp_path.parent / "elsewhere")


def test_sha256_known_value(tmp_path: Path) -> None:
    f = tmp_path / "x"
    f.write_bytes(b"abc")
    assert sha256_file(f) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
