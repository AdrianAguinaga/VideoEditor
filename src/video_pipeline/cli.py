"""`video-pipeline` CLI. Exit codes: 0 ok, 1 failure, 2 usage/ambiguity, 3 not configured, 4 tool error,
5 validation failed, 6 locked."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated, Any

import typer

from . import diagnostics, fixtures, runs
from . import ingest as ingest_mod
from . import render as render_mod
from . import timeline as tl
from .media import probe
from .transcribe import fetch_model, model_entry, model_ready, transcribe_input
from .util import PipelineError, UsageError, ValidationFailed, check_id, load_yaml, now_iso, sha256_file
from .workspace import Workspace, init_workspace, lock_state
from .workspace import unlock as unlock_video

app = typer.Typer(no_args_is_help=True, add_completion=False, pretty_exceptions_enable=False)
series_app = typer.Typer(no_args_is_help=True)
video_app = typer.Typer(no_args_is_help=True)
timeline_app = typer.Typer(no_args_is_help=True)
asset_app = typer.Typer(no_args_is_help=True)
models_app = typer.Typer(no_args_is_help=True)
schemas_app = typer.Typer(no_args_is_help=True)
for name, sub, text in [
    ("series", series_app, "Create/list series."),
    ("video", video_app, "Create videos."),
    ("timeline", timeline_app, "Scaffold, validate and review timelines."),
    ("asset", asset_app, "Register shared assets (cortinillas, logos...)."),
    ("models", models_app, "ASR model weights."),
    ("schemas", schemas_app, "JSON Schemas."),
]:
    app.add_typer(sub, name=name, help=text)

VideoArg = Annotated[str, typer.Argument(help="'serie/video' or a natural name such as 'clase 1 contabilidad'")]


def _ws() -> Workspace:
    return Workspace.find()


def _echo_checks(checks: list[Any]) -> None:
    for c in checks:
        mark = {"passed": "PASS", "failed": "FAIL", "skipped": "SKIP"}[c.status]
        typer.echo(f"  [{mark}] {c.name}: {c.detail}")


@app.command()
def init(name: Annotated[str, typer.Option(help="Workspace name")] = "video-workspace") -> None:
    """Create missing workspace files only. Safe to repeat: never overwrites."""
    root = Path.cwd()
    created = init_workspace(root, name)
    created += diagnostics.export_schemas(Workspace(root))
    typer.echo("\n".join(f"created {p.relative_to(root)}" for p in created) or "nothing to do: workspace complete")


@app.command()
def doctor(as_json: Annotated[bool, typer.Option("--json")] = False) -> None:
    """Report each component as missing / installed / detectable / configured / tested."""
    try:
        ws: Workspace | None = _ws()
    except PipelineError:
        ws = None
    checks = diagnostics.doctor(ws)
    if as_json:
        typer.echo(diagnostics.doctor_json(checks))
    else:
        for c in checks:
            typer.echo(f"{c.component:20} {c.state:11} {'required' if c.required else 'optional':8} {c.detail}")
    if any(c.required and not c.configured for c in checks):
        raise typer.Exit(1)


@app.command("bootstrap-check")
def bootstrap_check() -> None:
    """Read-only: list pending bootstrap actions (exit 1 if any)."""
    pending = diagnostics.bootstrap_pending(Path.cwd())
    typer.echo("\n".join(f"PENDING: {p}" for p in pending) or "bootstrap complete: nothing pending")
    if pending:
        raise typer.Exit(1)


@schemas_app.command("export")
def schemas_export() -> None:
    """Regenerate config/schemas/*.schema.json from the code contracts."""
    written = diagnostics.export_schemas(_ws())
    typer.echo("\n".join(f"wrote {p.name}" for p in written) or "schemas already up to date")


@models_app.command("fetch")
def models_fetch(name: Annotated[str, typer.Argument()] = "faster-whisper-medium") -> None:
    """Download pinned ASR weights into .local/models (skips if already present)."""
    ws = _ws()
    already = model_ready(ws, name)
    path = fetch_model(ws, name)
    typer.echo(f"{'already present' if already else 'downloaded'}: {path}")


@models_app.command("list")
def models_list() -> None:
    ws = _ws()
    for name in (load_yaml(ws.path("config/models.yaml")) or {}).get("models", {}):
        entry = model_entry(ws, name)
        state = "ready" if model_ready(ws, name) else "not downloaded"
        typer.echo(f"{name}: {entry['repo_id']}@{entry['revision'][:12]} ({entry['license']}) {state}")


@series_app.command("create")
def series_create(series_id: str, title: Annotated[str, typer.Option()]) -> None:
    path = _ws().create_series(check_id(series_id, "series id"), title)
    typer.echo(f"created series {series_id} at {path}")


@series_app.command("list")
def series_list() -> None:
    ws = _ws()
    for sid in ws.series_ids():
        s = ws.load_series(sid)
        typer.echo(f"{sid}: {s.title} ({len(s.videos)} videos: {', '.join(s.videos)})")


@video_app.command("create")
def video_create(series_id: str, video_id: str, title: Annotated[str, typer.Option()]) -> None:
    ref = _ws().create_video(series_id, check_id(video_id, "video id"), title)
    typer.echo(f"created video {ref.key} at {ref.dir}")


@app.command("resolve")
def resolve_cmd(video: VideoArg) -> None:
    """Show which 'serie/video' a natural name points to (exit 2 if ambiguous)."""
    typer.echo(_ws().resolve(video).key)


@asset_app.command("add")
def asset_add(
    file: Path,
    asset_id: Annotated[str, typer.Option("--id")],
    version: Annotated[int, typer.Option()],
    kind: Annotated[str, typer.Option()],
    license: Annotated[str, typer.Option()],
    permissions: Annotated[str, typer.Option()],
    role: Annotated[str | None, typer.Option()] = None,
    synthetic: Annotated[bool, typer.Option(help="mark as synthetic test fixture")] = False,
) -> None:
    rec = ingest_mod.register_asset(_ws(), file, asset_id, version, kind, license, permissions, role, synthetic)
    typer.echo(f"registered {rec.id}@{rec.version} sha256={rec.sha256[:12]} -> {rec.path}")


@app.command()
def ingest(
    video: VideoArg,
    file: Path,
    input_id: Annotated[str | None, typer.Option("--id")] = None,
    role: Annotated[str | None, typer.Option(help="originals|audio|slides|images|broll|scripts")] = None,
) -> None:
    """Copy a source into the video's inputs, verify its hash and make the copy read-only."""
    ws = _ws()
    rec = ingest_mod.ingest(ws, ws.resolve(video), file, input_id, role)  # type: ignore[arg-type]
    typer.echo(f"ingested {rec.id} ({rec.media.kind}, {rec.media.duration_ms} ms) sha256={rec.sha256[:12]}")


@app.command()
def inspect(
    video: Annotated[str | None, typer.Argument()] = None,
    file: Annotated[Path | None, typer.Option(help="probe any file instead")] = None,
) -> None:
    """Show normalized media info for a video's inputs (or one file)."""
    if file:
        typer.echo(probe(file).model_dump_json(indent=1))
        return
    if not video:
        raise UsageError("give a VIDEO or --file")
    ws = _ws()
    ref = ws.resolve(video)
    for rec in ws.inventory(ref).inputs:
        m = rec.media
        intact = sha256_file(ref.dir / rec.path) == rec.sha256
        typer.echo(
            f"{rec.id:20} {m.kind:5} {m.duration_ms} ms {m.width}x{m.height} fps={m.fps} "
            f"audio={m.sample_rate}Hz/{m.channels}ch codecs={','.join(m.codecs)} "
            f"original={rec.original_name} hash={'ok' if intact else 'CHANGED'}"
        )


@app.command()
def transcribe(video: VideoArg, input_id: str) -> None:
    """Run local ASR on an ingested input. Writes an immutable raw transcript."""
    ws = _ws()
    out = transcribe_input(ws, ws.resolve(video), input_id)
    typer.echo(f"transcript: {out}")


@timeline_app.command("scaffold")
def timeline_scaffold(
    video: VideoArg,
    name: str,
    source: Annotated[str, typer.Option()],
    still: Annotated[str | None, typer.Option()] = None,
    transcript: Annotated[str | None, typer.Option(help="path relative to the video dir")] = None,
) -> None:
    """Draft timeline from series/video style (intro + source + outro). Never overwrites."""
    ws = _ws()
    typer.echo(f"wrote {tl.scaffold(ws, ws.resolve(video), name, source, still, transcript)}")


@timeline_app.command("validate")
def timeline_validate(
    video: VideoArg, name: str, mode: Annotated[str, typer.Option(help="preview|master")] = "preview"
) -> None:
    ws = _ws()
    ref = ws.resolve(video)
    layout, warnings, _ = tl.resolve(ws, ref, tl.load_timeline(tl.timeline_path(ref, name)), mode)  # type: ignore[arg-type]
    for w in warnings:
        typer.echo(f"WARNING: {w}")
    typer.echo(f"valid for {mode}: {len(layout)} clips, {tl.output_duration(layout)} ms")


@timeline_app.command("review")
def timeline_review(video: VideoArg, name: str) -> None:
    """Readable edit list: clips with output positions, cuts with reason and removed text."""
    ws = _ws()
    ref = ws.resolve(video)
    timeline = tl.load_timeline(tl.timeline_path(ref, name))
    layout, warnings, _ = tl.resolve(ws, ref, timeline, "preview")
    typer.echo(tl.review_text(ref, timeline, layout, warnings))


def _render(video: str, name: str, mode: str, override: Path | None) -> None:
    ws = _ws()
    data = load_yaml(override) if override else None
    run_dir, run = render_mod.render(ws, ws.resolve(video), name, mode, data)  # type: ignore[arg-type]
    typer.echo(f"run {run.id}: {run.status}  ({run_dir})")
    _echo_checks(run.qa)
    for a in run.artifacts:
        typer.echo(f"  artifact {a.role}: {a.path}")
    typer.echo(f"next: {run.next_action}")
    if run.status != "succeeded":
        raise typer.Exit(1)


@app.command()
def preview(
    video: VideoArg,
    name: str,
    override: Annotated[Path | None, typer.Option(help="approved per-run settings override")] = None,
) -> None:
    """Render a low-res preview with burned subtitles into a new run."""
    _render(video, name, "preview", override)


@app.command()
def render(video: VideoArg, name: str, override: Annotated[Path | None, typer.Option()] = None) -> None:
    """Render master + delivery. Requires an approval for this exact timeline revision."""
    _render(video, name, "master", override)


@app.command()
def approve(
    video: VideoArg,
    run_id: str,
    actor: Annotated[str, typer.Option()],
    note: Annotated[str, typer.Option()] = "",
) -> None:
    """Record a human approval of one preview artifact (by hash). Run only after watching it."""
    ws = _ws()
    typer.echo(f"approval recorded: {runs.approve(ws.resolve(video), run_id, actor, note)}")


@app.command()
def qa(video: VideoArg, run_id: str) -> None:
    """Re-run technical QA on a run (integrity + checks) and save a report. Never edits the run."""
    ws = _ws()
    report, checks = render_mod.rerun_qa(ws, ws.resolve(video), run_id)
    _echo_checks(checks)
    typer.echo(f"report: {report}")
    if any(c.status == "failed" for c in checks):
        raise typer.Exit(1)


@app.command()
def status(video: Annotated[str | None, typer.Argument()] = None) -> None:
    """Where each video stands and what to do next. Also refreshes catalog/views/status.md."""
    ws = _ws()
    if video is None:
        lines = ["# Status (generated, do not edit)", "", f"_{now_iso()}_", ""]
        for _series, ref, cfg in ws.all_videos():
            run_list = runs.list_runs(ref)
            last = f"{run_list[-1][0].id} {run_list[-1][1]}" if run_list else "no runs"
            lines.append(f"- {ref.key} — {cfg.title} — inputs: {len(ws.inventory(ref).inputs)} — last run: {last}")
        text = "\n".join(lines) + "\n"
        (ws.root / "catalog/views").mkdir(parents=True, exist_ok=True)
        (ws.root / "catalog/views/status.md").write_text(text, "utf-8")
        typer.echo(text)
        return
    ref = ws.resolve(video)
    cfg = ws.load_video(ref)
    typer.echo(f"{ref.key} — {cfg.title} (privacy: {cfg.privacy})")
    state, info = lock_state(ref)
    typer.echo(f"lock: {state}{f' {info}' if info else ''}")
    for rec in ws.inventory(ref).inputs:
        typer.echo(f"input {rec.id} ({rec.media.kind}, {rec.media.duration_ms} ms)")
    for t in sorted((ref.dir / "editorial/transcript").glob("*.json")):
        typer.echo(f"transcript editorial/transcript/{t.name}")
    for t in sorted((ref.dir / "editorial/timelines").glob("*.yaml")):
        try:
            tl.resolve(ws, ref, tl.load_timeline(t), "preview", check_hashes=False)
            verdict = "valid"
        except (ValidationFailed, UsageError) as exc:
            verdict = f"INVALID ({str(exc).splitlines()[0]})"
        typer.echo(f"timeline {t.stem}: {verdict} sha256={sha256_file(t)[:12]}")
    for run, effective in runs.list_runs(ref):
        typer.echo(f"run {run.id}: {run.mode} {effective} timeline={run.timeline} next: {run.next_action}")
    for a in runs.approvals(ref):
        typer.echo(f"approval {a.id}: run {a.run_id} by {a.actor} timeline sha256={a.timeline_sha256[:12]}")
    if state == "stale":
        typer.echo(f"next: a previous process died holding the lock; run `video-pipeline unlock {ref.key}`")


@app.command()
def unlock(video: VideoArg) -> None:
    """Remove a stale lock left by a crashed process. Refuses if the owner is still alive."""
    ws = _ws()
    info = unlock_video(ws.resolve(video))
    typer.echo(f"lock removed: {info}" if info else "no lock present")


@app.command("fixtures")
def fixtures_cmd(out_dir: Path) -> None:
    """Generate small synthetic fixtures (test pattern, tone, slide, cortinilla) with FFmpeg."""
    for key, path in fixtures.generate(out_dir).items():
        typer.echo(f"{key}: {path}")


def main() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    try:
        app()
    except PipelineError as exc:
        typer.echo(f"error: {exc}", err=True)
        if exc.hint:
            typer.echo(f"hint: {exc.hint}", err=True)
        sys.exit(exc.exit_code)
