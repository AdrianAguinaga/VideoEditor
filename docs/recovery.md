# Recovery, locks and backups

## Resuming in a new session
1. `uv run video-pipeline bootstrap-check`: reports pending items without reinstalling anything.
2. `uv run video-pipeline status`: every video and its last run (also written to `catalog/views/status.md`).
3. `uv run video-pipeline status <serie/video>`: lock, inputs, transcripts, timelines (valid/invalid), runs, approvals, next action.

All state lives in files (`video.yaml`, `manifests/`, `editorial/`, `approvals/`, `runs/*/run.yaml`). There is no hidden memory.

## Interrupted runs and locks
- Each writer operation (ingest, transcript write, render) holds `series/<s>/videos/<v>/.lock` (pid, host, purpose, time). Only one writer per video.
- If a process dies, `status` shows `lock: stale` and the run as `interrupted`. Run `uv run video-pipeline unlock <video>` (it refuses if the owner process is still alive), then start a **new** run. The interrupted run stays as a record and is never reused.
- Exit codes: 6 = locked, 5 = validation, 4 = tool failure, 3 = not configured, 2 = usage.

## Backups (proposed policy, NOT implemented)
Git does **not** back up media: inputs, runs and transcripts are git-ignored on purpose.
Proposal: one copy of `series/` and `assets/` to an external disk or NAS with versioning (for example `robocopy series G:\backup\video-workspace\series /E /XO` plus snapshots). Do it after each ingest and each accepted master. A backup counts as real only after a restore of one video has been tested and its hashes match `manifests/inputs.yaml`.
**Status: no backup has been configured or tested.**

## Cleanup
Nothing is deleted automatically. `runs/*/work/` holds only the filter graph and a copy of the subtitles (small). Before deleting old runs, agree on a retention policy. Never delete `inputs/`, approved masters or `approvals/`.
