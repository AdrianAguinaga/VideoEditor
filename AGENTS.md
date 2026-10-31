# video-workspace: agent index

Local audiovisual production for course series (one series → introduction + classes). The engine is the Python package `video_pipeline` (`src/`), driven through the `video-pipeline` CLI. Agents propose; the CLI validates; people approve.

## Commands
- Setup / re-check: `powershell -File scripts/bootstrap.ps1` (idempotent) · `uv run video-pipeline bootstrap-check` · `uv run video-pipeline doctor`
- Video work: skill `video-series-editor` (canonical: `agent-capabilities/video-series-editor/`; full command table in `references/commands.md`)
- Start of any resumed session: `uv run video-pipeline status` and then `status <serie/video>`
- Quality gates: `uv run ruff check src tests scripts` · `uv run mypy` · `uv run pytest -q` · `uv run python scripts/sync_skills.py --check`

## Boundaries
- Never modify `series/*/videos/*/inputs/`, existing `runs/`, `approvals/` or raw `*.asr.json`. New work means a new file or run.
- `approve` is a human act. No publishing, uploads, external APIs, admin installs or global config changes without explicit approval.
- Editing the canonical skill → `uv run python scripts/sync_skills.py` (regenerates `.claude/skills` and `.agents/skills`; don't edit those copies).
- Changing `contracts.py` → `uv run video-pipeline schemas export` and commit `config/schemas/`.
- Engine logic belongs in `src/video_pipeline/`, not in prompts or skills.

## Map
`src/video_pipeline/`: `contracts` (schemas) · `workspace` (ids, precedence, locks) · `ingest` · `transcribe` · `timeline` (validation, remap) · `render` · `qa` · `runs` (runs, approvals) · `diagnostics` · `cli`
Docs: `docs/setup.md`, `docs/workflow.md`, `docs/recovery.md`, `docs/verification-report.md`, `docs/decisions/`
Engineering policy: `REQUIREMENTS_v3_investigacion_comparativa_agentes.md` (GSD/Ponytail baseline; do not add another methodology). Build contract: `REQUIREMENTS_bootstrap_video.md`.
