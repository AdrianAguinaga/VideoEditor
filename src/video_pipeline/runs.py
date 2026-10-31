"""Run records and human approvals. A run directory is created once and never reused."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .contracts import Approval, RunRecord
from .util import UsageError, ValidationFailed, load_yaml, now_iso, sha256_file, write_new_yaml, write_yaml
from .workspace import VideoRef, lock_state, parse

RUN_SUBDIRS = [
    "logs",
    "reports",
    "review",
    "work",
    "outputs/previews",
    "outputs/masters",
    "outputs/delivery",
    "outputs/subtitles",
    "outputs/thumbnails",
]


def create_run_dir(ref: VideoRef, mode: str) -> tuple[str, Path]:
    base = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{mode}"
    for n in range(1, 100):
        run_id = base if n == 1 else f"{base}-{n}"
        path = ref.dir / "runs" / run_id
        try:
            path.mkdir(parents=True)  # atomic: fails if another run already took this id
        except FileExistsError:
            continue
        for sub in RUN_SUBDIRS:
            (path / sub).mkdir(parents=True)
        return run_id, path
    raise UsageError("could not allocate a unique run id")


def save_run(run_dir: Path, run: RunRecord) -> None:
    write_yaml(run_dir / "run.yaml", run.model_dump(mode="json"))


def load_run(ref: VideoRef, run_id: str) -> tuple[Path, RunRecord]:
    run_dir = ref.dir / "runs" / run_id
    if not (run_dir / "run.yaml").is_file():
        raise UsageError(f"run {run_id!r} not found in {ref.key}")
    return run_dir, parse(RunRecord, load_yaml(run_dir / "run.yaml"), run_dir / "run.yaml")


def list_runs(ref: VideoRef) -> list[tuple[RunRecord, str]]:
    """(run, effective status). A `running` run without a live lock was interrupted."""
    runs_root = ref.dir / "runs"
    state, _ = lock_state(ref)
    result: list[tuple[RunRecord, str]] = []
    for path in sorted(runs_root.glob("*/run.yaml")):
        run = parse(RunRecord, load_yaml(path), path)
        status = "interrupted" if run.status == "running" and state != "held" else run.status
        result.append((run, status))
    return result


def approve(ref: VideoRef, run_id: str, actor: str, note: str = "") -> Path:
    """Record a human approval of one concrete preview artifact (by hash) and the timeline it came from."""
    run_dir, run = load_run(ref, run_id)
    if run.mode != "preview" or run.status != "succeeded":
        raise ValidationFailed(f"only a succeeded preview run can be approved ({run_id} is {run.mode}/{run.status})")
    artifact = next((a for a in run.artifacts if a.role == "preview"), None)
    if artifact is None:
        raise ValidationFailed(f"run {run_id} has no preview artifact")
    if sha256_file(run_dir / artifact.path) != artifact.sha256:
        raise ValidationFailed("the preview file changed after rendering; render a new preview")
    if not actor.strip():
        raise UsageError("an approval needs an --actor")
    approval_id = f"apr-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{run_id}"
    record = Approval(
        id=approval_id,
        video=ref.key,
        run_id=run_id,
        artifact=f"runs/{run_id}/{artifact.path}",
        artifact_sha256=artifact.sha256,
        timeline_sha256=run.timeline_sha256,
        actor=actor,
        approved_at=now_iso(),
        note=note,
    )
    path = ref.dir / "approvals" / f"{approval_id}.yaml"
    write_new_yaml(path, record.model_dump(mode="json"))
    return path


def approvals(ref: VideoRef) -> list[Approval]:
    folder = ref.dir / "approvals"
    return [parse(Approval, load_yaml(p), p) for p in sorted(folder.glob("*.yaml"))] if folder.is_dir() else []


def find_approval(ref: VideoRef, timeline_sha: str) -> Approval | None:
    matching = [a for a in approvals(ref) if a.timeline_sha256 == timeline_sha]
    return matching[-1] if matching else None
