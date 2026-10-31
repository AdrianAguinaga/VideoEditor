"""Timeline validation, output layout and subtitle remapping (source time -> output time)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from .contracts import (
    AssetClip,
    AssetRecord,
    Blur,
    InputRecord,
    Music,
    Overlay,
    Settings,
    SourceClip,
    Timeline,
    Transcript,
    Zoom,
)
from .media import system_font
from .util import UsageError, ValidationFailed, load_yaml, safe_join, sha256_file, write_new_yaml
from .workspace import VideoRef, Workspace, parse

Mode = Literal["preview", "master"]


@dataclass
class Placed:
    """A clip resolved against inventory/registry, with its position in the output."""

    clip: SourceClip | AssetClip
    out_start_ms: int
    duration_ms: int
    source: InputRecord | AssetRecord
    still: InputRecord | None = None
    blurs: list[Blur] = field(default_factory=list)  # those overlapping this clip's source range
    zooms: list[Zoom] = field(default_factory=list)
    background: AssetRecord | None = None  # style.background, source clips only

    @property
    def in_ms(self) -> int:
        return self.clip.in_ms


@dataclass
class Decor:
    """Timeline-wide layers, resolved to files and output time; applied after the clips are joined."""

    total_ms: int = 0
    overlays: list[tuple[Overlay, AssetRecord | None, list[tuple[int, int]]]] = field(default_factory=list)
    music: list[tuple[Music, AssetRecord]] = field(default_factory=list)
    fade_in_ms: int = 0
    fade_out_ms: int = 0
    font: Path | None = None  # system font for text overlays without a registered `font`


def output_duration(layout: list[Placed]) -> int:
    return layout[-1].out_start_ms + layout[-1].duration_ms if layout else 0


def output_ranges(layout: list[Placed], input_id: str, start_ms: int, end_ms: int | None) -> list[tuple[int, int]]:
    """Where a source range of `input_id` lands in the output (one piece per surviving clip)."""
    ranges = []
    for p in layout:
        if isinstance(p.clip, SourceClip) and p.clip.input == input_id:
            lo, hi = max(start_ms, p.clip.in_ms), min(end_ms if end_ms is not None else p.clip.out_ms, p.clip.out_ms)
            if hi > lo:
                ranges.append((p.out_start_ms + lo - p.clip.in_ms, p.out_start_ms + hi - p.clip.in_ms))
    return ranges


@dataclass
class Cue:
    start_ms: int
    end_ms: int
    text: str


def timeline_path(ref: VideoRef, name: str) -> Path:
    rel = name if name.endswith(".yaml") else f"editorial/timelines/{name}.yaml"
    return safe_join(ref.dir, rel)  # absolute paths are accepted only if inside the video directory


def load_timeline(path: Path) -> Timeline:
    if not path.is_file():
        raise UsageError(f"timeline not found: {path}")
    return parse(Timeline, load_yaml(path), path)


def load_transcript(ref: VideoRef, rel: str) -> Transcript:
    path = safe_join(ref.dir, rel)
    if not path.is_file():
        raise ValidationFailed(f"transcript not found: {rel}")
    return parse(Transcript, json.loads(path.read_text("utf-8")), path)


def resolve(
    ws: Workspace,
    ref: VideoRef,
    timeline: Timeline,
    mode: Mode = "preview",
    check_hashes: bool = True,
    settings: Settings | None = None,
) -> tuple[list[Placed], list[str], Decor]:
    """Validate every invariant needed before FFmpeg runs. Returns (layout, warnings, decor); raises on errors."""
    settings = settings or ws.settings(ref)
    errors: list[str] = []
    warnings: list[str] = []
    if timeline.video != ref.key:
        errors.append(f"timeline belongs to {timeline.video}, not {ref.key}")
    inputs = {i.id: i for i in ws.inventory(ref).inputs}
    assets = {(a.id, a.version): a for a in ws.registry().assets}
    hashed: set[str] = set()

    def verify_hash(path: Path, expected: str, label: str) -> None:
        if check_hashes and label not in hashed:
            hashed.add(label)
            if not path.is_file():
                errors.append(f"{label}: file missing ({path})")
            elif sha256_file(path) != expected:
                errors.append(f"{label}: file no longer matches its registered sha256")

    def asset_of(asset_id: str, version: int, kinds: tuple[str, ...], label: str) -> AssetRecord | None:
        asset = assets.get((asset_id, version))
        if asset is None or asset.kind not in kinds:
            errors.append(f"{label}: {asset_id}@{version} is not a registered {'/'.join(kinds)} asset")
            return None
        verify_hash(ws.path(asset.path), asset.sha256, f"asset {asset_id}@{version}")
        return asset

    style = settings.style
    background = None
    if style.background:
        background = asset_of(style.background.id, style.background.version, ("image", "logo"), "style.background")
        if background and (background.media is None or background.media.kind != "image"):
            errors.append(f"style.background: {background.id} is not an image")
    layout: list[Placed] = []
    cursor = 0
    for n, clip in enumerate(timeline.clips):
        label = f"clip {n}"
        if isinstance(clip, SourceClip):
            record = inputs.get(clip.input)
            if record is None:
                errors.append(f"{label}: input {clip.input!r} is not in this video's inventory")
                continue
            verify_hash(ref.dir / record.path, record.sha256, f"input {record.id}")
            if record.media.kind == "image":
                errors.append(f"{label}: image {clip.input!r} can only be used as `still`")
                continue
            duration = record.media.duration_ms or 0
            if clip.out_ms > duration:
                errors.append(f"{label}: out_ms {clip.out_ms} exceeds {clip.input} duration {duration}")
            still = None
            if clip.still:
                still = inputs.get(clip.still)
                if still is None or still.media.kind != "image":
                    errors.append(f"{label}: still {clip.still!r} must be an image input of this video")
                    still = None
                else:
                    verify_hash(ref.dir / still.path, still.sha256, f"input {still.id}")
            elif not record.media.has_video:
                warnings.append(f"{label}: audio-only source without `still`; background color will be used")
            length = clip.out_ms - clip.in_ms
            blurs = [
                b
                for b in timeline.blurs
                if b.input == clip.input and b.start_ms < clip.out_ms and b.end_ms > clip.in_ms
            ]
            zooms = [
                z
                for z in timeline.zooms
                if z.input == clip.input and z.start_ms < clip.out_ms and z.end_ms > clip.in_ms
            ]
            placed = Placed(clip, cursor, length, record, still, blurs, zooms, background)
        else:
            asset = assets.get((clip.asset, clip.version))
            if asset is None:
                errors.append(f"{label}: asset {clip.asset}@{clip.version} is not registered")
                continue
            verify_hash(ws.path(asset.path), asset.sha256, f"asset {clip.asset}@{clip.version}")
            if asset.media is None or asset.media.duration_ms is None:
                errors.append(f"{label}: asset {clip.asset} is not a timed media asset")
                continue
            end = clip.out_ms if clip.out_ms is not None else asset.media.duration_ms
            if end > asset.media.duration_ms:
                errors.append(f"{label}: out_ms {end} exceeds asset duration {asset.media.duration_ms}")
            length = end - clip.in_ms
            if length <= 0:
                errors.append(f"{label}: empty asset range")
                continue
            placed = Placed(clip, cursor, length, asset)
        if clip.transition:
            if not layout:
                errors.append(f"{label}: the first clip has nothing to transition from")
            elif clip.transition.ms >= min(length, layout[-1].duration_ms):
                errors.append(f"{label}: transition {clip.transition.ms} ms must be shorter than both clips")
            else:
                placed.out_start_ms -= clip.transition.ms  # the two clips overlap
        layout.append(placed)
        cursor = placed.out_start_ms + length

    for rel in timeline.transcripts:
        try:
            transcript = load_transcript(ref, rel)
        except ValidationFailed as exc:
            errors.append(str(exc))
            continue
        record = inputs.get(transcript.input_id)
        if record is None or record.sha256 != transcript.input_sha256:
            errors.append(f"transcript {rel} was made from a different version of {transcript.input_id}")
    for cut in timeline.cuts:
        if cut.input not in inputs:
            errors.append(f"cut {cut.start_ms}-{cut.end_ms}: unknown input {cut.input!r}")
    for b in [*timeline.blurs, *timeline.zooms]:
        what = f"{type(b).__name__.lower()} {b.start_ms}-{b.end_ms}"
        media = inputs[b.input].media if b.input in inputs else None
        if media is None or not media.has_video or media.width is None or media.height is None:
            errors.append(f"{what}: {b.input!r} is not a video input of this video")
        elif b.x + b.w > media.width or b.y + b.h > media.height:
            errors.append(f"{what}: box exceeds the {media.width}x{media.height} frame")
    total = output_duration(layout)
    decor = Decor(total, fade_in_ms=timeline.fade_in_ms, fade_out_ms=timeline.fade_out_ms)
    if timeline.fade_in_ms + timeline.fade_out_ms > total:
        errors.append(f"fade_in_ms + fade_out_ms exceed the {total} ms output")
    for k, o in enumerate(timeline.overlays):
        what = f"overlay {k}"
        image = None
        if o.asset is not None and o.version is not None:
            image = asset_of(o.asset, o.version, ("logo", "image"), what)
            if image and (image.media is None or image.media.kind != "image"):
                errors.append(f"{what}: {o.asset} is not an image")
        elif o.font is not None:
            image = asset_of(o.font.id, o.font.version, ("font",), what)  # the font file rides in the asset slot
        elif decor.font is None:
            decor.font = system_font()
            if decor.font is None:
                errors.append(f"{what}: no system font found; register one (`asset add --kind font`) and set `font`")
        if o.input is not None:
            if o.input not in inputs:
                errors.append(f"{what}: unknown input {o.input!r}")
            ranges = output_ranges(layout, o.input, o.start_ms, o.end_ms)
            if not ranges:
                warnings.append(f"{what}: its source range was cut entirely; it will not show")
        else:
            end = o.end_ms if o.end_ms is not None else total
            if end > total:
                errors.append(f"{what}: end_ms {end} exceeds the {total} ms output")
            ranges = [(o.start_ms, min(end, total))] if o.start_ms < total else []
        decor.overlays.append((o, image, ranges))
    for k, m in enumerate(timeline.music):
        track = asset_of(m.asset, m.version, ("music", "sfx"), f"music {k}")
        end = m.end_ms if m.end_ms is not None else total
        if m.start_ms >= total or end > total:
            errors.append(f"music {k}: range {m.start_ms}-{end} is outside the {total} ms output")
        elif track and (track.media is None or not track.media.has_audio):
            errors.append(f"music {k}: {m.asset} has no audio")
        elif track:
            decor.music.append((m.model_copy(update={"end_ms": end}), track))
    proposed = [c for c in timeline.cuts if c.status == "proposed"]
    if proposed and mode == "master":
        errors.append(f"{len(proposed)} cut(s) still `proposed`: accept or reject them before a master render")
    elif proposed:
        warnings.append(f"{len(proposed)} cut(s) are proposals, not approved edits")
    if errors:
        raise ValidationFailed("timeline is invalid:\n- " + "\n- ".join(errors))
    return layout, warnings, decor


def remap_cues(transcripts: list[Transcript], layout: list[Placed]) -> list[Cue]:
    """Map transcript segments that survive the edit onto output time. Cuts drop text; asset clips shift it."""
    by_input = {t.input_id: t for t in transcripts}
    cues: list[Cue] = []
    for placed in layout:
        clip = placed.clip
        if not isinstance(clip, SourceClip) or clip.input not in by_input:
            continue
        lo, hi = clip.in_ms, clip.out_ms
        for seg in by_input[clip.input].segments:
            if seg.end_ms <= lo or seg.start_ms >= hi:
                continue
            if seg.words:
                kept = [w for w in seg.words if lo <= (w.start_ms + w.end_ms) // 2 < hi]
                if not kept:
                    continue
                start, end = max(kept[0].start_ms, lo), min(kept[-1].end_ms, hi)
                text = " ".join(w.text for w in kept)
            else:
                start, end, text = max(seg.start_ms, lo), min(seg.end_ms, hi), seg.text
            out_start = placed.out_start_ms + start - lo
            out_end = placed.out_start_ms + end - lo
            if out_end > out_start and text.strip():
                cues.append(Cue(out_start, out_end, text.strip()))
    cues.sort(key=lambda c: c.start_ms)
    for prev, cur in zip(cues, cues[1:], strict=False):  # no overlaps in the output track
        if prev.end_ms > cur.start_ms:
            prev.end_ms = cur.start_ms
    return [c for c in cues if c.end_ms > c.start_ms]


def _stamp(ms: int, sep: str) -> str:
    h, rem = divmod(ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02}:{m:02}:{s:02}{sep}{ms:03}"


def to_srt(cues: list[Cue]) -> str:
    return "".join(
        f"{i}\n{_stamp(c.start_ms, ',')} --> {_stamp(c.end_ms, ',')}\n{c.text}\n\n" for i, c in enumerate(cues, 1)
    )


def to_vtt(cues: list[Cue]) -> str:
    body = "".join(f"{_stamp(c.start_ms, '.')} --> {_stamp(c.end_ms, '.')}\n{c.text}\n\n" for c in cues)
    return "WEBVTT\n\n" + body


def review_text(ref: VideoRef, timeline: Timeline, layout: list[Placed], warnings: list[str]) -> str:
    """Human-readable edit list: what stays, where it lands, and every cut with its reason and text."""
    transcripts = [load_transcript(ref, rel) for rel in timeline.transcripts]
    lines = [f"Timeline for {ref.key}", "", "CLIPS (output position <- source range)"]
    for p in layout:
        name = p.clip.input if isinstance(p.clip, SourceClip) else f"{p.clip.asset}@{p.clip.version}"
        t = p.clip.transition
        lines.append(
            f"  {_stamp(p.out_start_ms, '.')} +{p.duration_ms / 1000:.2f}s  {p.clip.kind:6} {name} "
            f"[{_stamp(p.in_ms, '.')} - {_stamp(p.in_ms + p.duration_ms, '.')})"
            + (f"  <- {t.type} {t.ms} ms" if t else "")
        )
    lines += ["", "CUTS (removed from source)"]
    if not timeline.cuts:
        lines.append("  (none)")
    for c in timeline.cuts:
        text = c.text or _text_between(transcripts, c.input, c.start_ms, c.end_ms)
        lines.append(
            f"  [{c.status:8}] {c.input} {_stamp(c.start_ms, '.')} - {_stamp(c.end_ms, '.')}  "
            f"reason: {c.reason}\n             text: {text or '(no speech)'}"
        )
    total = output_duration(layout)
    lines += ["", f"Output duration: {total / 1000:.2f}s"]
    lines += [f"WARNING: {w}" for w in warnings]
    return "\n".join(lines)


def _text_between(transcripts: list[Transcript], input_id: str, lo: int, hi: int) -> str:
    """Text removed by a cut: words by midpoint when available, otherwise every overlapping segment."""
    parts = []
    for seg in (s for t in transcripts if t.input_id == input_id for s in t.segments):
        if seg.words:
            parts += [w.text for w in seg.words if lo <= (w.start_ms + w.end_ms) // 2 < hi]
        elif seg.start_ms < hi and seg.end_ms > lo:
            parts.append(seg.text)
    return " ".join(parts)


def scaffold(
    ws: Workspace,
    ref: VideoRef,
    name: str,
    source: str,
    still: str | None = None,
    transcript: str | None = None,
) -> Path:
    """Draft timeline: series/video intro + the whole source + outro. Editing it is the agent's/editor's job."""
    style = ws.settings(ref).style
    record = next((i for i in ws.inventory(ref).inputs if i.id == source), None)
    if record is None or record.media.duration_ms is None:
        raise UsageError(f"input {source!r} is not a timed media input of {ref.key}")
    clips: list[dict[str, object]] = []
    if style.intro:
        clips.append({"kind": "asset", "asset": style.intro.id, "version": style.intro.version})
    clip: dict[str, object] = {
        "kind": "source",
        "input": source,
        "in_ms": 0,
        "out_ms": record.media.duration_ms,
    }
    if still:
        clip["still"] = still
    clips.append(clip)
    if style.outro:
        clips.append({"kind": "asset", "asset": style.outro.id, "version": style.outro.version})
    data = {
        "schema_version": 1,
        "video": ref.key,
        "transcripts": [transcript] if transcript else [],
        "subtitles": True,
        "clips": clips,
        "cuts": [],
    }
    parse(Timeline, data, "scaffold")
    path = timeline_path(ref, name)
    try:
        write_new_yaml(path, data)
    except FileExistsError:
        raise UsageError(f"timeline {name!r} already exists; pick a new name (timelines are versions)") from None
    return path
