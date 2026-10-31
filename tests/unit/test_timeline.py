"""Subtitle remapping and the ASR service with a fake backend (unit-level mock, clearly not ASR evidence)."""

import json
from pathlib import Path

import pytest

from video_pipeline.contracts import (
    AssetClip,
    AssetRecord,
    InputRecord,
    MediaInfo,
    Segment,
    SourceClip,
    Transcript,
    Word,
)
from video_pipeline.timeline import Placed, remap_cues, to_srt, to_vtt
from video_pipeline.transcribe import transcribe_input
from video_pipeline.util import NotConfigured, write_yaml
from video_pipeline.workspace import Workspace

SHA = "b" * 64
MEDIA = MediaInfo(kind="video", format_name="mp4", duration_ms=10_000, has_video=True, has_audio=True)
INPUT = InputRecord(
    id="grab",
    role="originals",
    original_name="g.mp4",
    path="inputs/originals/grab.mp4",
    sha256=SHA,
    size_bytes=1,
    ingested_at="t",
    media=MEDIA,
)
ASSET = AssetRecord(
    id="intro",
    version=1,
    kind="cortinilla",
    path="assets/x.mp4",
    sha256=SHA,
    license="x",
    permissions="x",
    registered_at="t",
    media=MEDIA,
)


def _w(s: int, e: int, t: str) -> Word:
    return Word(start_ms=s, end_ms=e, text=t)


def _transcript(segments: list[Segment]) -> Transcript:
    return Transcript.model_validate(
        {
            "video": "c/v",
            "input_id": "grab",
            "input_sha256": SHA,
            "language": "es",
            "duration_ms": 10_000,
            "created_at": "t",
            "segments": [s.model_dump() for s in segments],
            "backend": {
                "name": "fixture",
                "version": "0",
                "model": "none",
                "revision": None,
                "device": "n/a",
                "compute_type": "n/a",
            },
        }
    )


def test_remap_after_intro_and_cut() -> None:
    t = _transcript(
        [
            Segment(id=0, start_ms=0, end_ms=1000, text="uno dos", words=[_w(0, 400, "uno"), _w(500, 1000, "dos")]),
            Segment(id=1, start_ms=1200, end_ms=1800, text="eh eh", words=[_w(1200, 1500, "eh"), _w(1500, 1800, "eh")]),
            Segment(id=2, start_ms=2100, end_ms=3000, text="tres", words=[_w(2100, 3000, "tres")]),
        ]
    )
    layout = [
        Placed(AssetClip(asset="intro", version=1), 0, 2000, ASSET),  # 2 s cortinilla shifts everything
        Placed(SourceClip(input="grab", in_ms=0, out_ms=1100), 2000, 1100, INPUT),
        Placed(SourceClip(input="grab", in_ms=2000, out_ms=3000), 3100, 1000, INPUT),  # 1100-2000 cut out
    ]
    cues = remap_cues([t], layout)
    assert [(c.start_ms, c.end_ms, c.text) for c in cues] == [
        (2000, 3000, "uno dos"),
        (3200, 4100, "tres"),  # source 2100 -> 3100 + (2100 - 2000)
    ]


def test_remap_partial_words_and_no_overlap() -> None:
    t = _transcript(
        [
            Segment(
                id=0,
                start_ms=0,
                end_ms=2000,
                text="a b c d",
                words=[_w(0, 500, "a"), _w(500, 1000, "b"), _w(1000, 1500, "c"), _w(1500, 2000, "d")],
            ),
            Segment(id=1, start_ms=1900, end_ms=2500, text="e", words=[]),  # overlaps segment 0, no words
        ]
    )
    layout = [Placed(SourceClip(input="grab", in_ms=600, out_ms=2400), 0, 1800, INPUT)]
    cues = remap_cues([t], layout)
    assert cues[0].text == "b c d"  # "a" (midpoint 250) falls in the removed head
    assert cues[0].start_ms == 0  # clipped to the clip start
    assert cues[0].end_ms <= cues[1].start_ms  # no overlap in output
    assert cues[1].end_ms == 1800  # segment without words is clipped to the clip end


def test_srt_and_vtt_format() -> None:
    from video_pipeline.timeline import Cue

    cues = [Cue(3_723_004, 3_724_500, "Hola")]
    assert to_srt(cues) == "1\n01:02:03,004 --> 01:02:04,500\nHola\n\n"
    assert to_vtt(cues).startswith("WEBVTT\n\n01:02:03.004 --> 01:02:04.500\nHola")


class FakeTranscriber:
    """Unit-test double. Its output is never treated as ASR verification."""

    def transcribe(self, media: Path, language: str):
        return [Segment(id=0, start_ms=0, end_ms=500, text="hola")], {"duration_ms": 1000}


def test_transcript_is_immutable_and_fake_does_not_mark_verified(ws: Workspace, tmp_path: Path) -> None:
    ws.create_series("s", "S")
    ref = ws.create_video("s", "v", "V")
    src = ref.dir / "inputs/audio/a.wav"
    src.write_bytes(b"x")
    from video_pipeline.util import sha256_file

    rec = INPUT.model_copy(update={"id": "a", "path": "inputs/audio/a.wav", "sha256": sha256_file(src)})
    write_yaml(ref.dir / "manifests/inputs.yaml", {"video": "s/v", "inputs": [rec.model_dump(mode="json")]})
    out = transcribe_input(ws, ref, "a", transcriber=FakeTranscriber())
    data = json.loads(out.read_text("utf-8"))
    assert data["segments"][0]["text"] == "hola" and data["input_sha256"] == rec.sha256
    assert not (ws.root / ".local/state/asr-verified.json").exists()


def test_missing_model_is_not_configured(ws: Workspace, monkeypatch: pytest.MonkeyPatch) -> None:
    from video_pipeline.contracts import AsrSettings
    from video_pipeline.transcribe import FasterWhisperTranscriber

    monkeypatch.setenv("VIDEO_PIPELINE_MODELS_DIR", str(ws.root / "empty"))
    with pytest.raises(NotConfigured, match="not downloaded"):
        FasterWhisperTranscriber(ws, AsrSettings())


def test_blur_hides_box_only_in_its_time_range(tmp_path: Path) -> None:
    """A blur smooths its rectangle while active and leaves the rest of the frame and other times untouched."""
    import shutil
    import subprocess

    from video_pipeline.contracts import Blur, Profile, Settings
    from video_pipeline.render import build_graph
    from video_pipeline.workspace import VideoRef

    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg not available")
    src = tmp_path / "inputs/originals/grab.mp4"
    src.parent.mkdir(parents=True)
    ff = ["ffmpeg", "-v", "error", "-y"]
    pattern = "color=c=gray:s=320x240:r=30:d=2,noise=alls=80:allf=t+u"  # detail everywhere
    subprocess.run(
        [*ff, "-f", "lavfi", "-i", pattern, "-f", "lavfi", "-i", "sine=d=2", "-shortest", str(src)], check=True
    )
    media = MEDIA.model_copy(update={"duration_ms": 2000, "width": 320, "height": 240})
    record = INPUT.model_copy(update={"media": media})
    blur = Blur(input="grab", start_ms=1000, end_ms=2000, x=0, y=0, w=160, h=120, reason="test")
    placed = Placed(SourceClip(input="grab", in_ms=0, out_ms=2000), 0, 2000, record, blurs=[blur])
    profile = Profile(width=320, height=240, fps=30)
    args, graph = build_graph([placed], None, VideoRef("c", "v", tmp_path), profile, Settings(), "master", False)  # type: ignore[arg-type]
    out = tmp_path / "out.mp4"
    subprocess.run([*ff, *args, "-filter_complex", graph, "-map", "[vout]", "-map", "[aout]", str(out)], check=True)

    def box_detail(t: float, x: int) -> float:
        raw = subprocess.run(
            [
                *ff[:3],
                "-ss",
                str(t),
                "-i",
                str(out),
                "-frames:v",
                "1",
                "-vf",
                f"crop=160:120:{x}:0,format=gray",
                "-f",
                "rawvideo",
                "-",
            ],
            capture_output=True,
            check=True,
        ).stdout
        return sum(abs(raw[i] - raw[i + 1]) for i in range(len(raw) - 1)) / len(raw)  # mean horizontal gradient

    assert box_detail(1.5, 0) < box_detail(0.5, 0) / 3  # blurred while active
    assert box_detail(1.5, 160) > box_detail(1.5, 0) * 3  # neighbouring area stays sharp


def test_transition_after_joins_keeps_audio_in_sync(tmp_path: Path) -> None:
    """Frame padding at joins, afftdn latency and the loudnorm tail must not move audio away from video."""
    import shutil
    import subprocess

    from video_pipeline.contracts import AudioSettings, Profile, Settings, Transition
    from video_pipeline.render import build_graph
    from video_pipeline.workspace import VideoRef

    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg not available")
    src = tmp_path / "inputs/originals/grab.mp4"
    src.parent.mkdir(parents=True)
    ff = ["ffmpeg", "-v", "error", "-y"]
    subprocess.run(
        [
            *ff,
            "-f",
            "lavfi",
            "-i",
            "testsrc2=s=320x240:r=30:d=6",
            "-f",
            "lavfi",
            "-i",
            "aevalsrc='if(gte(t,0.3),0.5*sin(2*PI*300*t),0)':s=48000:d=6",  # a tone that starts at 300 ms
            "-shortest",
            str(src),
        ],
        check=True,
    )
    record = INPUT.model_copy(update={"media": MEDIA.model_copy(update={"duration_ms": 6000})})
    layout, cursor = [], 0
    for k in range(6):  # 550 ms = 16.5 frames: every join pads half a frame
        clip = SourceClip(input="grab", in_ms=k * 550, out_ms=(k + 1) * 550)
        layout.append(Placed(clip, cursor, 550, record))
        cursor += 550
    last = SourceClip(
        input="grab", in_ms=3300, out_ms=5341, transition=Transition(ms=300)
    )  # odd length, like real clips
    layout.append(Placed(last, cursor - 300, 2041, record))
    profile = Profile(width=320, height=240, fps=30)
    audio = AudioSettings(highpass_hz=80, denoise_db=10, compress=True, loudness_lufs=-16, edge_fade_ms=15)
    args, graph = build_graph(
        layout,
        None,
        VideoRef("c", "v", tmp_path),
        profile,
        Settings(audio=audio),
        "master",
        False,  # type: ignore[arg-type]
    )
    out = tmp_path / "out.mp4"
    subprocess.run([*ff, *args, "-filter_complex", graph, "-map", "[vout]", "-map", "[aout]", str(out)], check=True)
    pcm = subprocess.run(
        [*ff[:3], "-i", str(out), "-t", "0.5", "-ac", "1", "-ar", "48000", "-f", "s16le", "-"],
        capture_output=True,
        check=True,
    ).stdout
    samples = [int.from_bytes(pcm[i : i + 2], "little", signed=True) for i in range(0, len(pcm), 2)]
    loudest = max(map(abs, samples))
    onset_ms = next(i for i, x in enumerate(samples) if abs(x) > loudest / 4) / 48
    assert abs(onset_ms - 300) < 10, onset_ms  # the voice stays on its picture
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,duration", "-of", "csv=p=0", str(out)],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    durations = {kind: float(sec) for kind, sec in (line.split(",") for line in probe.split())}
    expected = (cursor - 300 + 2041) / 1000
    assert abs(durations["video"] - expected) < 0.034 and abs(durations["audio"] - expected) < 0.034, durations
