# Environment report (G0 — read-only diagnosis)

Date: 2026-10-27 · Gathered by: Claude Code (Opus 5.5) · Nothing installed or modified during G0.

## Platform
| Item | Observed |
|---|---|
| OS | Windows 11 Pro 10.0.26300 |
| Shells | PowerShell 5.1.26100 (ExecutionPolicy: Bypass), Git Bash |
| CPU | AMD Ryzen 7 5700X — 8 cores / 16 threads |
| RAM | 31.9 GB |
| GPU | AMD Radeon RX 6600 (driver 32.0.21045.16010) — **no NVIDIA/CUDA** (`nvidia-smi` absent) |
| Disk | E: 99 GB free (workspace), C: 1.47 TB free, G: 1.4 TB free |
| Long paths | `LongPathsEnabled = 0` → keep workspace paths short (< 260 chars) |

## Workspace
- `E:\skills\VideoEditor` — **not a Git repository**. Contains only the two REQUIREMENTS files (user-authored, not modified).
- Greenfield project: no existing code, so no characterization tests needed.

## Toolchain
| Tool | Version | Path | Notes |
|---|---|---|---|
| git | 2.51.0.windows.1 | system | |
| Python | 3.11.9, 3.13.7 (`py` default 3.13) | `%LOCALAPPDATA%\Programs\Python` | `python3` is the Store alias stub, so don't use it |
| uv | 0.12.18 | `%LOCALAPPDATA%\hermes\bin\uv` | installed by another tool ("hermes"); works, but it isn't on a standard path |
| FFmpeg / ffprobe | 9.0.2 full_build (gyan.dev) | WinGet Links | GPL build; x264, x265, libass, freetype, harfbuzz, opus, **`--enable-whisper`** (whisper.cpp filter), AMF (AMD HW encode) |
| Node.js | 24.22.1 | Program Files | not required unless a graphics engine is chosen |
| Claude Code | 2.1.311 | `~/.local/bin` | |
| Codex CLI | 0.164.0 | npm global | |
| winget | present | | no choco/scoop |

## ASR implications
- faster-whisper uses CTranslate2, whose GPU support is **CUDA only**. On this machine it runs on **CPU** (`device=cpu`, `compute_type=int8`).
- CTranslate2 4.8.4 ships Windows wheels for cp39–cp315, so Python 3.11 or 3.13 both work.
- Alternative observed: FFmpeg's built-in `whisper` filter (whisper.cpp, can use Vulkan on AMD). Recorded as a possible later backend; not selected for the base (the contract names faster-whisper first).

## Resolved upstream versions (PyPI / Hugging Face, queried 2026-10-27)
| Package / model | Version / revision | License |
|---|---|---|
| faster-whisper | 1.2.1 | MIT |
| ctranslate2 | 4.8.4 | MIT |
| pydantic | 2.14.1 | MIT |
| typer | 0.27.3 | MIT |
| PyYAML | 6.0.3 | MIT |
| pytest | 9.1.1 | MIT |
| ruff | 0.17.3 | MIT |
| Systran/faster-whisper-small | `536b066…` | MIT |
| Systran/faster-whisper-medium | `08e178d…` | MIT |

## Engineering methodology (from REQUIREMENTS v3)
GSD skills, Ponytail (global CLAUDE.md), Graphify, and Matt Pocock skills (code-review, diagnosing-bugs, codebase-design) are present at user level. They are kept as the baseline and are not reinstalled. Global Claude/Codex configuration is not modified.

## Privacy / network
- Network is reachable (PyPI, Hugging Face). Network egress is limited to package and model downloads. No media leaves the machine.
- No secrets were read.

## Pending decisions / blockers
1. Approval of the bootstrap plan (installs, model download size).
2. ASR model size (small vs medium).
3. **Authorized Spanish voice sample**: none present yet. Real-ASR validation stays blocked until one is provided.
4. `git init` of the workspace.
