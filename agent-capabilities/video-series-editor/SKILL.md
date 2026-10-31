---
name: video-series-editor
description: Edit videos of a course/series in this workspace with the local `video-pipeline` CLI (ingest, Spanish transcription, timeline with reviewable cuts, cortinillas, preview, approval, master render, QA). Use when the user asks to add, transcribe, cut, preview, render, check or resume a video, class or series ("la clase 2 del curso de contabilidad"). Do not use for publishing or uploading videos.
---

# Video series editor

The engine is the `video-pipeline` package (run as `uv run video-pipeline ...` from the workspace root).
This skill only drives it; never reimplement FFmpeg logic in prompts.

## 1. Resolve the target first
- `uv run video-pipeline resolve "<what the user said>"` → `serie/video`. Exit 2 = ambiguous: show the options and ask.
- `uv run video-pipeline status <serie/video>` → inputs, transcripts, timelines, runs (incl. `interrupted`), approvals, lock, next action. Start every resumed session here.

## 2. Operations (they all exist; see references/commands.md)
`doctor`, `bootstrap-check`, `series create`, `video create`, `ingest`, `inspect`, `transcribe`, `timeline scaffold|validate|review`, `preview`, `approve`, `render`, `qa`, `status`, `unlock`, `asset add`.

## 3. Editing workflow
1. `ingest` sources (copied + hashed; originals never modified).
2. `transcribe <video> <input>` → immutable `editorial/transcript/*.asr.json`.
3. Write a **new** timeline file (`editorial/timelines/vN.yaml`). Never edit a timeline that has an approval; copy it to a new name. Format: references/timeline.md.
   Production layers (transitions, zooms, overlays/lower thirds, music, fades) also live in the timeline; background, voice cleanup, loudness and color are series/video settings. Propose them like cuts: the person decides.
4. Put every removal in `cuts` with `reason`, `text` and `status: proposed`. You propose; the person decides.
5. `timeline review` → show the person the readable cut list. `timeline validate`.
6. `preview` → give the person the preview path. Wait for them to watch it.
7. Only when the person says it is approved: `approve <video> <run> --actor "<their name>"`. Change accepted cuts to `accepted` and rejected ones to `rejected` in the **timeline file before the final preview**, since approval binds to the timeline hash.
8. `render` (master + delivery) and report the QA lines verbatim.

## 4. Editorial policy (conservative)
Propose: false starts, repetitions, clear errors, long dead air. Preserve: negations, numbers/figures, steps of a procedure, pedagogical pauses. Silence detection is not a decision about pacing. Read `series/<s>/glossary.yaml` for terms.

## 5. Limits: ask first
- Never run `approve` on your own judgment. Approval is a human act.
- No uploads, publishing, external APIs, deleting inputs/runs/outputs, editing `inputs/`, or `--force` of any kind.
- `unlock` only when `status` says the lock is stale.
- Report failures with the exit code and stderr. A failed QA check is never "basically fine".
  Exit codes: 2 usage/ambiguous, 3 not configured, 4 tool failed, 5 validation failed, 6 locked.
