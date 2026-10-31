# video-pipeline

Reusable, local platform for editing course video series: series → videos (introduction, classes) → ingest → Spanish transcription → timeline with reviewable cuts → cortinillas → preview with remapped subtitles → human approval → master/delivery → technical QA.

Everything runs locally: FFmpeg, and faster-whisper on CPU. No external APIs, no publishing.

## Quick start (Windows)
```powershell
powershell -File scripts\bootstrap.ps1   # idempotent: install from uv.lock, init, models, tests
uv run video-pipeline doctor
uv run video-pipeline status
```

## First video
```powershell
uv run video-pipeline series create curso-contabilidad --title "Curso de Contabilidad"
uv run video-pipeline video create curso-contabilidad clase-001 --title "Clase 1: El balance"
uv run video-pipeline ingest "clase 1 contabilidad" D:\grabaciones\clase1.mp4 --id grabacion
uv run video-pipeline transcribe "clase 1 contabilidad" grabacion
uv run video-pipeline timeline scaffold "clase 1 contabilidad" v1 --source grabacion --transcript editorial/transcript/<file>.asr.json
# edit cuts in a new timeline (or ask Claude/Codex: skill video-series-editor)
uv run video-pipeline timeline review "clase 1 contabilidad" v1
uv run video-pipeline preview "clase 1 contabilidad" v1
uv run video-pipeline approve "clase 1 contabilidad" <run-id> --actor "Tu Nombre"   # after watching it
uv run video-pipeline render "clase 1 contabilidad" v1
```

More: [docs/setup.md](docs/setup.md) · [docs/workflow.md](docs/workflow.md) · [docs/recovery.md](docs/recovery.md) · [docs/verification-report.md](docs/verification-report.md) · [AGENTS.md](AGENTS.md)
