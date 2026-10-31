"""Renderer: turns a validated timeline into one FFmpeg filter graph and records a traceable run.

Every clip is normalized (size, fps, sample rate, exact duration) and joined in a single encode (concat, or
xfade/acrossfade where a clip has a transition), so output positions match the timeline layout used to remap
subtitles. Timeline-wide layers (overlays, music, fades, loudness) are applied to the joined result.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from .contracts import Artifact, AssetRecord, ColorSettings, Profile, QaCheck, Region, RunRecord, Settings
from .media import run_tool, tool, tool_version
from .qa import check_subtitles, check_video
from .runs import create_run_dir, find_approval, load_run, save_run
from .timeline import (
    Decor,
    Mode,
    Placed,
    load_timeline,
    load_transcript,
    output_duration,
    remap_cues,
    resolve,
    timeline_path,
    to_srt,
    to_vtt,
)
from .util import PipelineError, ValidationFailed, dump_yaml, now_iso, sha256_file, write_new_yaml
from .workspace import VideoRef, Workspace, video_lock

# overlay x:y for each position; W/H frame, w/h the overlaid thing, m the margin in pixels
_POSITIONS = {
    "top-left": ("{m}", "{m}"),
    "top": ("({W}-{w})/2", "{m}"),
    "top-right": ("{W}-{w}-{m}", "{m}"),
    "center": ("({W}-{w})/2", "({H}-{h})/2"),
    "bottom-left": ("{m}", "{H}-{h}-{m}"),
    "bottom": ("({W}-{w})/2", "{H}-{h}-{m}"),
    "bottom-right": ("{W}-{w}-{m}", "{H}-{h}-{m}"),
}


_DENOISE_DELAY_MS = 25  # afftdn delays its output by half its 50 ms window (measured, any rate/strength)


def _sec(ms: int) -> str:
    return f"{ms / 1000:.3f}"


def _even(x: float) -> int:
    return max(2, int(x) // 2 * 2)


def _window(r: Region, p: Placed) -> str:
    """enable= expression for a source-time region inside a clip (t restarts at 0 for each seeked input)."""
    start, end = _sec(max(r.start_ms - p.in_ms, 0)), _sec(min(r.end_ms, p.in_ms + p.duration_ms) - p.in_ms)
    return f"between(t,{start},{end})"


def overlay_files(ws: Workspace, decor: Decor | None) -> dict[str, str | Path]:
    """Files drawtext reads from work/: text (no filtergraph escaping) and font (no Windows drive escaping)."""
    files: dict[str, str | Path] = {}
    for k, (o, font, _) in enumerate(decor.overlays if decor else []):
        if o.text and decor:
            font_path = ws.path(font.path) if font else decor.font
            if font_path is None:  # timeline.resolve reports this; guard against misuse
                raise ValidationFailed(f"overlay {k} has no font")
            files[f"overlay-{k}.txt"] = o.text
            files[f"overlay-{k}{font_path.suffix.lower()}"] = font_path
    return files


def build_graph(
    layout: list[Placed],
    ws: Workspace,
    ref: VideoRef,
    profile: Profile,
    settings: Settings,
    mode: Mode,
    burn_subtitles: bool,
    decor: Decor | None = None,
) -> tuple[list[str], str]:
    """Return (input args, filter graph). Pure function of the validated layout: easy to inspect/test."""
    w, h, fps, sr = profile.width, profile.height, profile.fps, profile.sample_rate
    style, audio = settings.style, settings.audio
    bg = style.background_color
    c = settings.color
    eq = (
        f"eq=brightness={c.brightness}:contrast={c.contrast}:saturation={c.saturation}:gamma={c.gamma},"
        if c != ColorSettings()
        else ""
    )
    args: list[str] = []
    chains: list[str] = []
    index = 0

    def add_input(*extra: str) -> int:
        nonlocal index
        args.extend(extra)
        index += 1
        return index - 1

    def looped(path: Path, dur: str) -> int:  # a still image as a clip-long video input
        return add_input("-loop", "1", "-framerate", str(fps), "-t", dur, "-i", str(path))

    for n, p in enumerate(layout):
        dur = _sec(p.duration_ms)
        is_source = not isinstance(p.source, AssetRecord)
        path = ref.dir / p.source.path if is_source else ws.path(p.source.path)
        media = p.source.media
        if media is None:  # timeline.resolve rejects untimed assets; guard against misuse
            raise ValidationFailed(f"clip {n} has no media info")
        denoise = bool(audio.denoise_db) and is_source and media.has_audio
        read = p.duration_ms + (_DENOISE_DELAY_MS if denoise else 0)  # the video is trimmed to `dur` anyway
        main = add_input("-ss", _sec(p.in_ms), "-t", _sec(read), "-i", str(path))
        picture = True
        if media.has_video:
            v_in = f"[{main}:v:0]"
            for k, b in enumerate(p.blurs):
                tag = f"b{n}_{k}"
                chains.append(
                    f"{v_in}split=2[{tag}base][{tag}crop];"
                    f"[{tag}crop]crop={b.w}:{b.h}:{b.x}:{b.y},gblur=sigma=20[{tag}blur];"
                    f"[{tag}base][{tag}blur]overlay={b.x}:{b.y}:enable='{_window(b, p)}'[{tag}]"
                )
                v_in = f"[{tag}]"
            for k, z in enumerate(p.zooms):  # after blurs, so a blurred box stays hidden when zoomed
                tag, iw, ih = f"z{n}_{k}", media.width, media.height
                chains.append(
                    f"{v_in}split=2[{tag}base][{tag}crop];"
                    f"[{tag}crop]crop={z.w}:{z.h}:{z.x}:{z.y},"
                    f"scale={iw}:{ih}:force_original_aspect_ratio=increase,crop={iw}:{ih}[{tag}zoom];"
                    f"[{tag}base][{tag}zoom]overlay=0:0:enable='{_window(z, p)}'[{tag}]"
                )
                v_in = f"[{tag}]"
        elif p.still is not None:
            v_in = f"[{looped(ref.dir / p.still.path, dur)}:v]"
        elif p.background is not None:
            v_in = f"[{looped(ws.path(p.background.path), dur)}:v]"
            picture = False
        else:
            v_in = f"[{add_input('-f', 'lavfi', '-t', dur, '-i', f'color=c={bg}:s={w}x{h}:r={fps}')}:v]"
            picture = False
        tail = (
            f"setsar=1,fps={fps},format=yuv420p,tpad=stop_mode=clone:stop_duration={dur},trim=duration={dur},"
            f"setpts=PTS-STARTPTS[v{n}]"
        )
        styled = is_source and picture
        scale = (100 - style.inset_pct) / 100 if styled else 1
        pw, ph = (_even(w * scale), _even(h * scale)) if scale < 1 else (w, h)
        fit = f"{eq if styled else ''}scale={pw}:{ph}:force_original_aspect_ratio=decrease"
        cover = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}"
        if styled and (p.background is not None or style.background_blur):
            if p.background is not None:
                chains.append(f"[{looped(ws.path(p.background.path), dur)}:v]{cover},setsar=1[bg{n}]")
                chains.append(f"{v_in}{fit},setsar=1[fg{n}]")
            else:
                chains.append(f"{v_in}split=2[fs{n}][bs{n}];[bs{n}]{cover},gblur=sigma=40,setsar=1[bg{n}]")
                chains.append(f"[fs{n}]{fit},setsar=1[fg{n}]")
            chains.append(f"[bg{n}][fg{n}]overlay=(W-w)/2:(H-h)/2:shortest=1,{tail}")
        else:
            chains.append(f"{v_in}{fit},pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color={bg},{tail}")
        a_in = (
            f"[{main}:a:0]"
            if media.has_audio
            else f"[{add_input('-f', 'lavfi', '-t', dur, '-i', f'anullsrc=r={sr}:cl=stereo')}:a]"
        )
        voice = ""
        if is_source and media.has_audio:
            voice += f"highpass=f={audio.highpass_hz}," if audio.highpass_hz else ""
            voice += (
                f"afftdn=nr={audio.denoise_db},atrim=start={_sec(_DENOISE_DELAY_MS)},asetpts=PTS-STARTPTS,"
                if denoise
                else ""
            )
            voice += "acompressor=threshold=0.1:ratio=3:attack=5:release=200:makeup=2," if audio.compress else ""
        edge = audio.edge_fade_ms
        edges = (
            f",afade=t=in:d={_sec(edge)},afade=t=out:st={_sec(p.duration_ms - edge)}:d={_sec(edge)}"
            if edge and 2 * edge < p.duration_ms
            else ""
        )
        chains.append(
            f"{a_in}{voice}aresample={sr},aformat=sample_fmts=fltp:channel_layouts=stereo,apad,atrim=duration={dur},"
            f"asetpts=PTS-STARTPTS{edges}[a{n}]"
        )

    if any(p.clip.transition for p in layout):
        v, a = "[v0]", "[a0]"
        for n, p in enumerate(layout[1:], 1):
            t = p.clip.transition
            if t:
                # Joins pad clips to whole frames; cutting both streams at the exact timeline point keeps them in sync.
                end = _sec(p.out_start_ms + t.ms)
                chains.append(
                    f"{v}trim=duration={end}[vt{n}];"
                    f"[vt{n}][v{n}]xfade=transition={t.type}:duration={_sec(t.ms)}:offset={_sec(p.out_start_ms)}[vj{n}]"
                )
                chains.append(f"{a}atrim=duration={end}[at{n}];[at{n}][a{n}]acrossfade=d={_sec(t.ms)}[aj{n}]")
            else:
                chains.append(  # concat output has a 1/1000000 timebase; a later xfade needs 1/fps
                    f"{v}{a}[v{n}][a{n}]concat=n=2:v=1:a=1[vk{n}][aj{n}];[vk{n}]settb=1/{fps}[vj{n}]"
                )
            v, a = f"[vj{n}]", f"[aj{n}]"
        chains.append(f"{v}null[vc]")
        chains.append(f"{a}anull[ac]")
    else:
        pairs = "".join(f"[v{n}][a{n}]" for n in range(len(layout)))
        chains.append(f"{pairs}concat=n={len(layout)}:v=1:a=1[vc][ac]")

    total = output_duration(layout)
    vlast, alast = "[vc]", "[ac]"
    for k, (o, image, ranges) in enumerate(decor.overlays if decor else []):
        if not ranges:
            continue
        enable = "+".join(f"between(t,{_sec(s)},{_sec(e)})" for s, e in ranges)
        m = round(h * o.margin_pct / 100)
        if o.asset is not None and image is not None:
            x, y = (s.format(W="W", H="H", w="w", h="h", m=m) for s in _POSITIONS[o.position])
            img = add_input("-i", str(ws.path(image.path)))  # a single frame, repeated by overlay
            chains.append(
                f"[{img}:v]scale={_even(w * o.size_pct / 100)}:-2,format=rgba,colorchannelmixer=aa={o.opacity}[ov{k}];"
                f"{vlast}[ov{k}]overlay={x}:{y}:enable='{enable}'[vo{k}]"
            )
        else:
            x, y = (s.format(W="w", H="h", w="tw", h="th", m=m) for s in _POSITIONS[o.position])
            size = round(h * o.size_pct / 100)
            box = f"box=1:boxcolor={o.box_color}:boxborderw={size // 2}" if o.box_color else "box=0"
            font = ws.path(image.path) if image else (decor.font if decor else None)
            if font is None:  # timeline.resolve reports this; guard against misuse
                raise ValidationFailed(f"overlay {k} has no font")
            chains.append(
                f"{vlast}drawtext=textfile=overlay-{k}.txt:fontfile=overlay-{k}{font.suffix.lower()}:expansion=none:fontsize={size}:"
                f"fontcolor={o.color}@{o.opacity}:line_spacing={size // 4}:{box}:x={x}:y={y}:enable='{enable}'[vo{k}]"
            )
        vlast = f"[vo{k}]"

    music = decor.music if decor else []
    if music:
        beds = []
        ducked = [k for k, (mu, _) in enumerate(music) if mu.duck]
        if ducked:
            chains.append(f"{alast}asplit={len(ducked) + 1}[voice]" + "".join(f"[sc{k}]" for k in ducked))
            alast = "[voice]"
        for k, (mu, track) in enumerate(music):
            length = (mu.end_ms or total) - mu.start_ms
            fade = _sec(min(mu.fade_ms, length // 2))
            src = add_input("-stream_loop", "-1", "-t", _sec(length), "-i", str(ws.path(track.path)))
            chains.append(
                f"[{src}:a]aresample={sr},aformat=sample_fmts=fltp:channel_layouts=stereo,volume={mu.volume_db}dB,"
                f"afade=t=in:d={fade},afade=t=out:st={_sec(length - min(mu.fade_ms, length // 2))}:d={fade},"
                f"adelay=delays={mu.start_ms}:all=1,apad,atrim=duration={_sec(total)}[m{k}]"
            )
            if mu.duck:
                chains.append(f"[m{k}][sc{k}]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=500[m{k}d]")
                beds.append(f"[m{k}d]")
            else:
                beds.append(f"[m{k}]")
        chains.append(f"{alast}{''.join(beds)}amix=inputs={len(beds) + 1}:duration=first:normalize=0[amix]")
        alast = "[amix]"

    vpost, apost = [], []
    if audio.loudness_lufs is not None:
        apost.append(  # loudnorm pads its last 100 ms block: trim back to the timeline length
            f"loudnorm=I={audio.loudness_lufs}:TP={audio.true_peak_db}:LRA=11,aresample={sr},atrim=duration={_sec(total)}"
        )
    fin, fout = (decor.fade_in_ms, decor.fade_out_ms) if decor else (0, 0)
    if fin:
        vpost.append(f"fade=t=in:d={_sec(fin)}")
        apost.append(f"afade=t=in:d={_sec(fin)}")
    if fout:
        vpost.append(f"fade=t=out:st={_sec(total - fout)}:d={_sec(fout)}")
        apost.append(f"afade=t=out:st={_sec(total - fout)}:d={_sec(fout)}")
    if mode == "preview":
        vpost.append(f"scale=-2:{profile.preview_height}")
    if burn_subtitles:
        vpost.append("subtitles=subs.srt")  # relative: ffmpeg runs with cwd=work/ (avoids Windows drive escaping)
    chains.append(f"{vlast}{','.join(vpost) or 'null'}[vout]")
    chains.append(f"{alast}{','.join(apost) or 'anull'}[aout]")
    return args, ";\n".join(chains)


def render(
    ws: Workspace, ref: VideoRef, timeline_name: str, mode: Mode, override: dict[str, Any] | None = None
) -> tuple[Path, RunRecord]:
    tpath = timeline_path(ref, timeline_name)
    timeline = load_timeline(tpath)
    timeline_sha = sha256_file(tpath)
    settings = ws.settings(ref, override)
    profile = ws.profile(settings.profile)
    layout, warnings, decor = resolve(ws, ref, timeline, mode, settings=settings)
    approval = None
    if mode == "master":
        approval = find_approval(ref, timeline_sha)
        if approval is None:
            raise ValidationFailed(
                "no approval matches this exact timeline revision",
                hint="render a preview of this timeline, review it, then `video-pipeline approve VIDEO RUN_ID`",
            )
    cues = remap_cues([load_transcript(ref, t) for t in timeline.transcripts], layout) if timeline.subtitles else []
    expected = output_duration(layout)
    used = [p.source for p in layout if isinstance(p.source, AssetRecord)]
    used += [p.background for p in layout if p.background] + [a for _, a, _ in decor.overlays if a]
    used += [a for _, a in decor.music]
    name = f"{ref.series}_{ref.video}"

    with video_lock(ref, f"render {mode}"):
        run_id, run_dir = create_run_dir(ref, mode)
        run = RunRecord(
            id=run_id,
            video=ref.key,
            mode=mode,
            status="running",
            started_at=now_iso(),
            timeline=tpath.relative_to(ref.dir).as_posix(),
            timeline_sha256=timeline_sha,
            approval=approval.id if approval else None,
            expected_duration_ms=expected,
            inputs={p.source.id: p.source.sha256 for p in layout if not isinstance(p.source, AssetRecord)}
            | {p.still.id: p.still.sha256 for p in layout if p.still},
            assets={f"{a.id}@{a.version}": a.sha256 for a in used},
            tools={"ffmpeg": tool_version("ffmpeg")},
        )
        save_run(run_dir, run)
        write_new_yaml(
            run_dir / "resolved-config.yaml",
            {
                "settings": settings.model_dump(mode="json"),
                "profile": profile.model_dump(mode="json"),
                "override": override,
                "warnings": warnings,
            },
        )
        log = run_dir / "logs/ffmpeg.log"
        try:
            artifacts = _execute(ws, ref, run_dir, run, layout, decor, profile, settings, mode, cues, name, log)
            run.artifacts = [
                Artifact(
                    role=role,
                    path=p.relative_to(run_dir).as_posix(),
                    sha256=sha256_file(p),
                    size_bytes=p.stat().st_size,
                )
                for role, p in artifacts
            ]
            run.qa = _qa(run_dir, run, profile, settings, mode, log)
            failed = [c.name for c in run.qa if c.status == "failed"]
            run.status = "failed" if failed else "succeeded"
            if failed:
                run.next_action = f"technical QA failed ({', '.join(failed)}); see reports/ and logs/"
            elif mode == "preview":
                run.next_action = (
                    f"human review of the preview, then `video-pipeline approve {ref.key} {run_id}` "
                    "and `video-pipeline render`"
                )
            else:
                run.next_action = "delivery ready in outputs/delivery (technical QA passed; publishing is manual)"
            if not failed:
                _mark_render_verified(ws, run_id)
        except PipelineError as exc:
            run.status, run.error = "failed", str(exc)
            run.next_action = "fix the error and start a new run (this run is kept as a record)"
            raise
        finally:
            run.finished_at = now_iso()
            save_run(run_dir, run)
    return run_dir, run


def _execute(
    ws: Workspace,
    ref: VideoRef,
    run_dir: Path,
    run: RunRecord,
    layout: list[Placed],
    decor: Decor,
    profile: Profile,
    settings: Settings,
    mode: Mode,
    cues: list,
    name: str,
    log: Path,
) -> list[tuple[str, Path]]:
    work = run_dir / "work"
    artifacts: list[tuple[str, Path]] = []
    if cues:
        srt, vtt = run_dir / f"outputs/subtitles/{name}.srt", run_dir / f"outputs/subtitles/{name}.vtt"
        srt.write_text(to_srt(cues), "utf-8")
        vtt.write_text(to_vtt(cues), "utf-8")
        shutil.copyfile(srt, work / "subs.srt")
        artifacts += [("subtitles-srt", srt), ("subtitles-vtt", vtt)]
    burn = mode == "preview" and bool(cues)
    for file, content in overlay_files(ws, decor).items():
        if isinstance(content, Path):
            shutil.copyfile(content, work / file)
        else:
            (work / file).write_bytes(content.encode("utf-8"))  # LF only: drawtext draws a CR as an extra line
    inputs, graph = build_graph(layout, ws, ref, profile, settings, mode, burn, decor)
    (work / "graph.txt").write_text(graph, "utf-8")
    if mode == "preview":
        out = run_dir / f"outputs/previews/{name}_preview.mp4"
        quality = ["-preset", "veryfast", "-crf", "28"]
    else:
        out = run_dir / f"outputs/masters/{name}.mp4"
        quality = ["-preset", profile.preset, "-crf", str(profile.crf)]
    argv = [
        tool("ffmpeg"),
        "-nostdin",
        "-hide_banner",
        "-y",
        *inputs,
        "-/filter_complex",
        "graph.txt",
        "-map",
        "[vout]",
        "-map",
        "[aout]",
        "-c:v",
        profile.video_codec,
        *quality,
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        profile.audio_bitrate,
        "-ar",
        str(profile.sample_rate),
        "-ac",
        "2",
        "-movflags",
        "+faststart",
        str(out),
    ]
    run.commands.append(argv)
    run_tool(argv, log=log, cwd=work)
    artifacts.append(("preview" if mode == "preview" else "master", out))
    if mode == "master":
        thumb = run_dir / f"outputs/thumbnails/{name}.jpg"
        thumb_argv = [
            tool("ffmpeg"),
            "-nostdin",
            "-hide_banner",
            "-y",
            "-ss",
            _sec((run.expected_duration_ms or 0) // 2),
            "-i",
            str(out),
            "-frames:v",
            "1",
            "-q:v",
            "3",
            str(thumb),
        ]
        run.commands.append(thumb_argv)
        run_tool(thumb_argv, log=log)
        artifacts.append(("thumbnail", thumb))
        for role, src in [("delivery", out)] + [
            (f"delivery-{r}", p) for r, p in artifacts if r.startswith("subtitles")
        ]:
            dest = run_dir / "outputs/delivery" / src.name
            shutil.copy2(src, dest)
            artifacts.append((role, dest))
    return artifacts


def _qa(run_dir: Path, run: RunRecord, profile: Profile, settings: Settings, mode: Mode, log: Path) -> list[QaCheck]:
    role = "preview" if mode == "preview" else "master"
    video = next(run_dir / a.path for a in run.artifacts if a.role == role)
    # A preview's width follows the aspect ratio, so only its height is fixed.
    width = profile.width if mode == "master" else None
    height = profile.height if mode == "master" else profile.preview_height
    checks = check_video(
        video,
        expected_ms=run.expected_duration_ms,
        width=width,
        height=height,
        tolerance_ms=settings.qa.duration_tolerance_ms,
        log=log,
    )
    srt = next((run_dir / a.path for a in run.artifacts if a.role == "subtitles-srt"), None)
    checks.append(
        check_subtitles(srt, run.expected_duration_ms)
        if srt
        else QaCheck(name="subtitles", status="skipped", detail="timeline has no transcript/subtitles")
    )
    checks.append(
        QaCheck(
            name="human_acceptance",
            status="skipped",
            detail="not a technical check: requires `video-pipeline approve` by a person",
        )
    )
    return checks


def rerun_qa(ws: Workspace, ref: VideoRef, run_id: str) -> tuple[Path, list[QaCheck]]:
    """Re-check a finished run without changing it: artifact integrity + technical checks, saved as a report."""
    run_dir, run = load_run(ref, run_id)
    settings = ws.settings(ref)
    profile = ws.profile(settings.profile)
    checks = [
        QaCheck(
            name=f"integrity:{a.path}",
            status="passed" if (run_dir / a.path).is_file() and sha256_file(run_dir / a.path) == a.sha256 else "failed",
            detail="sha256 matches run record",
        )
        for a in run.artifacts
    ]
    checks += _qa(run_dir, run, profile, settings, run.mode, run_dir / "logs/qa.log")
    report = run_dir / "reports" / f"qa-{now_iso().replace(':', '')}.yaml"
    report.write_text(dump_yaml([c.model_dump() for c in checks]), "utf-8")
    return report, checks


def _mark_render_verified(ws: Workspace, run_id: str) -> None:
    state = ws.path(".local/state/render-verified.json")
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(json.dumps({"run": run_id, "at": now_iso()}), "utf-8")
