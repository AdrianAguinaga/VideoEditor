# Commands (all implemented; run from the workspace root with `uv run video-pipeline ...`)

| Command | What it does | Writes |
|---|---|---|
| `doctor [--json]` | Shows each component as missing / installed / detectable / configured / tested | nothing |
| `bootstrap-check` | Lists pending setup actions (exit 1 if any) | nothing |
| `init` | Creates missing workspace files only | missing files |
| `models list` / `models fetch NAME` | Pinned ASR weights | `.local/models/` |
| `schemas export` | Regenerates JSON Schemas from code | `config/schemas/` |
| `series create ID --title T` / `series list` | Series and canonical video order | `series/ID/`, catalog |
| `video create SERIES ID --title T` | New video skeleton | `series/S/videos/ID/` |
| `resolve "natural name"` | Maps a name to `serie/video` (exit 2 if ambiguous) | nothing |
| `asset add FILE --id --version --kind --license --permissions [--role] [--synthetic]` | Immutable id@version asset | `assets/` |
| `ingest VIDEO FILE [--id] [--role]` | Copies and hash-checks a source; the copy is read-only | `inputs/`, `manifests/inputs.yaml` |
| `inspect VIDEO` / `inspect --file F` | Media info and hash integrity | nothing |
| `transcribe VIDEO INPUT` | Local faster-whisper ASR (es, CPU int8) | `editorial/transcript/*.asr.json` |
| `timeline scaffold VIDEO NAME --source IN [--still IMG] [--transcript P]` | Draft: intro + source + outro | new timeline |
| `timeline validate VIDEO NAME [--mode master]` | All invariants before FFmpeg | nothing |
| `timeline review VIDEO NAME` | Readable clips and cuts with removed text | nothing |
| `preview VIDEO NAME [--override F]` | 480p preview with burned subtitles, in a new run | `runs/<id>/` |
| `approve VIDEO RUN --actor NAME [--note]` | **Human** approval of a preview (by hash) | `approvals/` |
| `render VIDEO NAME [--override F]` | Master + thumbnail + delivery (needs an approval) | `runs/<id>/` |
| `qa VIDEO RUN` | Re-checks integrity and technical QA | `runs/<id>/reports/` |
| `status [VIDEO]` | State and next action; refreshes `catalog/views/status.md` | the view only |
| `unlock VIDEO` | Removes a **stale** lock only | `.lock` |
| `fixtures DIR` | Synthetic test media | DIR |

VIDEO accepts `serie/video` or a natural name ("clase 2 contabilidad").
Exit codes: 0 ok · 1 failed (incl. QA) · 2 usage/ambiguous · 3 not configured · 4 tool failed · 5 validation · 6 locked.
