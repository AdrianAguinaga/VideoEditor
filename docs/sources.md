# Sources actually consulted during implementation (2026-10-27)

| Source | URL | Used for |
|---|---|---|
| PyPI JSON API | https://pypi.org/pypi/{faster-whisper,ctranslate2,pydantic,typer,pyyaml,pytest,ruff}/json | current versions, Python ranges, MIT licenses; ctranslate2 4.8.4 Windows wheels cp39–cp315 |
| Hugging Face API | https://huggingface.co/api/models/Systran/faster-whisper-medium | revision `08e178d48790749d25932bbc082711ddcfdfbc4f`, MIT license |
| Hugging Face API | https://huggingface.co/api/models/Systran/faster-whisper-small | evaluated, not downloaded |
| Claude Code skills | https://code.claude.com/docs/en/skills | `.claude/skills/<name>/SKILL.md`; `description` recommended |
| Codex skills | https://learn.chatgpt.com/docs/build-skills (redirected from developers.openai.com/codex/skills) | `.agents/skills/` from CWD up to repo root; `name` and `description` required |
| Installed package APIs | `inspect.signature` on huggingface_hub 2.3.0 `snapshot_download` and faster_whisper 1.2.1 | download and transcribe parameters |
| Local FFmpeg | `ffmpeg -version / -encoders / -filters` (9.0.2 gyan full_build) | capabilities: libx264, aac, libass, `-/filter_complex` file syntax |

Not consulted (listed in the contract as starting points, not needed for the decisions taken): the faster-whisper/WhisperX/Whisper GitHub READMEs, the FFmpeg docs site, watzing/claude-video-editor. Revisit WhisperX if alignment is ever needed.
