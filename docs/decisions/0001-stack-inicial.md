# ADR 0001: Initial stack

Date: 2026-10-27 · Status: accepted (plan approved by the user)

## Decisions
1. **Python 3.13 + uv** (`uv.lock` is the only lockfile; no requirements.txt). uv was already installed. ctranslate2 publishes cp313 wheels.
2. **ASR: faster-whisper 1.2.1, model `Systran/faster-whisper-medium` (multilingual, MIT), CPU int8.** The GPU is an AMD RX 6600, and CTranslate2 only accelerates on CUDA. `medium` was the user's choice over `small`, for Spanish accuracy.
3. **No WhisperX / no diarization** for now. The contract allows it (`Aligner` = `not_configured`). Revisit only if the preview shows word-level cut errors that matter.
4. **Graphics: FFmpeg only.** Cortinillas are registered video assets. No Remotion/HyperFrames, and Node is not required. Text title cards are not implemented yet (they would need a licensed font asset).
5. **One FFmpeg filter graph per render** (normalize → concat → single encode). Output positions are exact, so subtitle remapping is exact. Clip-by-clip encoding plus concat copy was rejected because of per-segment AAC drift.
6. **Time = integer milliseconds, half-open ranges.**
7. **Approval binds to the timeline sha256 and the preview sha256.** Any edit to the timeline invalidates it.
8. **Skill adapters = generated copies** (`scripts/sync_skills.py`, checked in tests). Symlinks were rejected because they need Developer Mode or admin on Windows.

## Alternative noted
The FFmpeg 9 build includes a `whisper` filter (whisper.cpp, which can use Vulkan on AMD). It is a possible faster backend for this GPU. Evaluate it against faster-whisper on the same Spanish sample before adopting it.
