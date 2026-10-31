# Verification report

Date: 2026-10-27 · Machine: Windows 11 Pro, Ryzen 7 5700X, 32 GB, AMD RX 6600 (no CUDA)
Plan approved by the user: G1–G5, ASR model `medium`, local `git init`, Spanish sample supplied by the user.

## Status by phase
| Phase | Status | Evidence |
|---|---|---|
| G0 Diagnosis | ✅ | `docs/environment-report.md` |
| G1 Environment | ✅ | `uv.lock` (47 packages), `.venv` Python 3.13.14, faster-whisper 1.2.1 / ctranslate2 4.8.4, `medium` weights (1.53 GB, rev `08e178d`), `config/toolchain.lock.yaml` |
| G2 Minimum engine | ✅ except real ASR | CLI with 24 commands, 11 versioned schemas, preview/master/QA running on real FFmpeg |
| G3 Multi-video | ✅ | `curso-piloto` with introduccion / clase-001 / clase-002 rendered in isolation; cortinilla inherited from the series; repeated bootstrap without changes |
| G4 Agents | ✅ discovery · ⏳ evals | Claude Code 2.1.311 and Codex 0.164.0 found and used `video-series-editor` (see below). With/without-skill evaluation: pending |
| G5 Handoff | ✅ | README, setup, workflow, recovery, sources, ADR 0001 |

## Executed and observed
- `scripts/bootstrap.ps1` complete: exit 0. `uv sync --locked` (no-op), `init` "nothing to do", `models fetch` "already present", `bootstrap-check` "nothing pending", ruff OK, mypy OK, adapters in sync, **pytest 38 passed, 1 skipped**.
- Integration tests (real FFmpeg, CLI as a subprocess, no mocks):
  - Three videos isolated: each run only references its own inputs. Outputs stay inside their video. Source files keep their hash. Ingested copies are read-only.
  - Accepted cut + 2 s cortinilla + subtitles: SRT remapped exactly (2,100→3,900 and 4,200→6,800 ms). Text from the cut does not appear.
  - `render` without an approval → exit 5. An approval from an earlier timeline revision → exit 5. With a valid approval → master + thumbnail + delivery (mp4/srt/vtt).
  - New cortinilla version: re-registering the same `id@version` → exit 2. Earlier runs keep `@1` with the same hash.
  - Failures: corrupt source → exit 5, nothing copied. Duplicate ingest → 2. Invalid timeline (out of range, unknown input, missing asset) → 5 and FFmpeg never runs. Missing model → 3. Tampered original → 5. Ambiguous name → 2.
  - Deliberately truncated master: `qa` → exit 1 with `integrity` and `decodes` FAIL.
  - Stale lock: blocks with exit 6 and an `unlock` hint. `status` shows `stale`. `unlock` + new preview OK. Interrupted run detected as `interrupted`.
  - Repeated bootstrap: identical hashes for every file in the workspace.
- Visual check of a preview frame: the source timestamp matches the output position after the cut, and the subtitle is burned in.
- Agent adapters:
  - `claude -p` (new session): used the `video-series-editor` skill, ran `resolve` + `status` and gave the correct next step (6 turns, USD 0.24).
  - `codex exec --sandbox read-only`: listed and used `video-series-editor` from `.agents/skills`, ran `status` (8,291 tokens).

## Blocked / pending
| Item | Status | What unblocks it |
|---|---|---|
| **Real ASR in Spanish** | ⛔ NOT verified: `doctor` reports `configured`, not `tested` | Authorized sample from the user → `VIDEO_PIPELINE_ASR_SAMPLE=<path> uv run pytest -m asr` and `transcribe` |
| Approve + master in the real workspace | pending | a person watches the pilot preview and approves it |
| Media backup | not implemented (proposal in recovery.md) | choose a destination and test a restore |
| With/without-skill evaluation | pending (`evals/`) | once real classes go through the flow |
| Local browser editor | not built (allowed as a later phase) | CLI flow validated first |
| Title cards with text | not implemented | a font with a license recorded in `assets/` |
| macOS/Linux | unverified | — |

## Deliberately excluded
WhisperX, diarization, Remotion/HyperFrames, Node, CUDA, publishing to social networks, external APIs, global installs and global Claude/Codex config.

## Known limitations
- Word timestamps from Whisper are approximate (~100–300 ms). Check cuts in the preview.
- ASR on CPU: the `medium` model is slower than real time on CPU. Expect minutes per class, not seconds.
- `assets/registry.yaml` is written without a global lock: avoid registering assets from two processes at once.
- `manifests/inputs.yaml` and `run.yaml` record original file names and hashes, and `run.yaml` records absolute paths in `commands`. Review them before sharing the repository.
