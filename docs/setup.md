# Setup and rebuild

Verified only on: **Windows 11 Pro, PowerShell 5.1, Git Bash** (2026-10-27). macOS and Linux are **unverified**. The core is portable (argv-only subprocesses, pathlib), but `scripts/bootstrap.ps1` is PowerShell-only. On other systems, run the same steps by hand.

## Prerequisites (system level, not installed by the bootstrap)
| Tool | How | Notes |
|---|---|---|
| uv | https://docs.astral.sh/uv/ | it manages Python 3.13 by itself |
| FFmpeg + ffprobe | `winget install Gyan.FFmpeg` | needs libx264, aac, libass (`subtitles`) |

## Steps (`scripts/bootstrap.ps1` does all of them)
1. `uv sync --locked`: creates `.venv` exactly from `uv.lock`, including the `video-pipeline` package in editable mode.
2. `uv run video-pipeline init`: creates only missing workspace files.
3. `uv run video-pipeline models fetch faster-whisper-medium`: ~1.5 GB, MIT, pinned revision from `config/models.yaml`, stored in `.local/models/`. Skipped if already present.
4. `uv run video-pipeline bootstrap-check`: read-only list of what is still pending.
5. Lint, types, adapter sync and tests (`-SkipTests` to omit).

Options: `-CheckOnly` (read-only), `-NoDownload`, `-SkipTests`.

## Where things live
| What | Where | In Git |
|---|---|---|
| Python deps | `pyproject.toml` + `uv.lock` | yes |
| Binaries | `config/toolchain.lock.yaml` (recorded, not installed) | yes |
| Models | `config/models.yaml` → `.local/models/` | registry yes, weights **no** |
| Media, runs, transcripts | `series/*/videos/*/{inputs,runs,editorial/transcript}` | **no** (see recovery.md) |

## Updating (a separate, deliberate action)
`uv lock --upgrade-package faster-whisper` → `uv sync` → run the full tests and the real ASR test → record the change in `docs/decisions/`. The bootstrap never upgrades anything.

## Network
Only `uv sync` (PyPI) and `models fetch` (huggingface.co) use the network. Media never leaves the machine. Once the weights exist, set `HF_HUB_OFFLINE=1` to forbid Hugging Face access.

## Rollback
Delete `.venv/` and `.local/`. Nothing outside the project folder is modified.
