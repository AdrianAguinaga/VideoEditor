@AGENTS.md

## Claude Code specifics
- The project skill is discovered from `.claude/skills/video-series-editor/` (a generated copy; edit `agent-capabilities/`).
- Use the Bash tool for `uv run video-pipeline ...`. The shell is Windows: prefer forward slashes and quote paths that contain spaces.
- Do not load the REQUIREMENTS files whole into subagents; cite the relevant section.
