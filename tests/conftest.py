from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from video_pipeline import fixtures
from video_pipeline.diagnostics import export_schemas
from video_pipeline.workspace import Workspace, init_workspace

PROJECT = Path(__file__).resolve().parents[1]


@pytest.fixture
def ws(tmp_path: Path) -> Workspace:
    root = tmp_path / "ws"
    init_workspace(root, "test-workspace")
    shutil.copyfile(PROJECT / "config/models.yaml", root / "config/models.yaml")
    workspace = Workspace(root)
    export_schemas(workspace)  # same end state as `video-pipeline init`
    return workspace


@pytest.fixture(scope="session")
def media(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    """Synthetic FFmpeg fixtures, generated once per session."""
    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg not available")
    return fixtures.generate(tmp_path_factory.mktemp("media"))


def cli(root: Path, *args: str | Path) -> subprocess.CompletedProcess[str]:
    """Run the real CLI as a subprocess so exit codes and stderr are the ones a user sees."""
    env = {**os.environ, "PYTHONUTF8": "1"}
    env.pop("VIDEO_PIPELINE_WORKSPACE", None)
    return subprocess.run(
        [sys.executable, "-m", "video_pipeline", *map(str, args)],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        check=False,
    )
