import re
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
SKILL = PROJECT / "agent-capabilities/video-series-editor/SKILL.md"


def test_adapters_in_sync_with_canonical_skill() -> None:
    result = subprocess.run(
        [sys.executable, PROJECT / "scripts/sync_skills.py", "--check"], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stdout


def test_skill_frontmatter_and_commands_exist() -> None:
    text = SKILL.read_text("utf-8")
    assert text.startswith("---\nname: video-series-editor\ndescription: ")  # Codex requires both fields
    import typer.main

    from video_pipeline.cli import app

    group = typer.main.get_command(app)
    names = set(group.commands)  # type: ignore[attr-defined]
    for sub in ("series", "video", "timeline", "asset", "models", "schemas"):
        names |= {f"{sub} {c}" for c in group.commands[sub].commands}  # type: ignore[attr-defined]
    documented = re.findall(
        r"^\| `([a-z-]+(?: [a-z-]+)?)", (SKILL.parent / "references/commands.md").read_text("utf-8"), re.M
    )
    for cmd in documented:
        first = cmd if cmd in names else cmd.split()[0]
        assert first in names, f"documented command {cmd!r} does not exist"


def test_documented_models_fetch_is_idempotent() -> None:
    from tests.conftest import cli

    if not (PROJECT / ".local/models/faster-whisper-medium/model.bin").is_file():
        import pytest

        pytest.skip("weights not downloaded in this checkout")
    result = cli(PROJECT, "models", "fetch", "faster-whisper-medium")  # must not download again
    assert result.returncode == 0 and "already present" in result.stdout, result.stderr
