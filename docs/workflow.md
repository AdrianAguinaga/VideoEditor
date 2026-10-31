# Production workflow

## Organization
- `catalog/series.yaml` lists the series. `series/<id>/series.yaml` holds the **canonical video order** and the series defaults (style/background, audio cleanup and loudness, color, profile, ASR; see the skill's `references/timeline.md`).
- Each video (`series/<s>/videos/<v>/video.yaml`) holds its title, privacy and its own `overrides`.
- Settings precedence: `config/workspace.yaml defaults` < `series.yaml defaults` < `video.yaml overrides` < `--override file.yaml` for a single run (saved in `runs/<id>/resolved-config.yaml`).
- Commands accept `serie/video` or a natural name ("clase 2 contabilidad"). An ambiguous name gives exit 2 and the list of candidates.

## Steps
| # | Step | Command | Result |
|---|---|---|---|
| 1 | Ingest | `ingest VIDEO FILE --id x [--role slides]` | read-only copy + sha256 in `manifests/inputs.yaml` |
| 2 | Transcribe | `transcribe VIDEO x` | `editorial/transcript/x.<ts>.asr.json` (immutable) |
| 3 | Draft | `timeline scaffold VIDEO v1 --source x --transcript ...` | intro (series style) + source + outro |
| 4 | Propose cuts | agent or person writes `v2.yaml` with `cuts: status: proposed` | — |
| 5 | Review | `timeline review VIDEO v2` | clip list and cuts with reason and removed text |
| 6 | Preview | `preview VIDEO v2` | 480p + burned subtitles in `runs/<id>/` |
| 7 | Decide | mark each cut `accepted`/`rejected` (new timeline file) → preview again | — |
| 8 | Approve | `approve VIDEO RUN --actor NAME` | `approvals/*.yaml` bound to preview hash + timeline hash |
| 9 | Master | `render VIDEO v3` | master, thumbnail, delivery (mp4 + srt + vtt), QA |
| 10 | Check | `qa VIDEO RUN` | integrity + technical QA report |

## Cortinillas and shared assets
`asset add FILE --id cortinilla-entrada --version 2 --kind cortinilla --role entrada --license ... --permissions ...`.
`id@version` is immutable. To change a cortinilla, register a new version and update `series.yaml` → `defaults.style.intro`. Existing timelines and runs keep the version they pinned.

## Editorial policy
The agent **proposes** removals (errors, repetitions, false starts). It preserves negations, figures, procedure steps and pedagogical pauses. Silence detection is not a pacing decision. Only `accepted` cuts can reach a master.

## Technical QA vs. human acceptance
QA checks decoding, streams, resolution, duration (±100 ms: 1 frame at 30 fps + 1 AAC frame + margin), non-silent audio, and subtitle bounds and overlaps. It never approves editorially: `human_acceptance` always shows SKIP until a person runs `approve`.
