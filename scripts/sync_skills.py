"""Copy the canonical skill to each agent's project discovery path, or check that the copies are in sync.

Canonical:  agent-capabilities/<skill>/
Claude Code: .claude/skills/<skill>/  (https://code.claude.com/docs/en/skills)
Codex CLI:   .agents/skills/<skill>/  (https://learn.chatgpt.com/docs/build-skills)
Only touches these project-local folders; never user/global skill directories.

usage: python scripts/sync_skills.py [--check]
"""

from __future__ import annotations

import filecmp
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "agent-capabilities"
TARGETS = [ROOT / ".claude/skills", ROOT / ".agents/skills"]


def files(base: Path) -> set[Path]:
    return {p.relative_to(base) for p in base.rglob("*") if p.is_file()}


def drift() -> list[str]:
    problems = []
    for skill in (p for p in CANONICAL.iterdir() if p.is_dir()):
        for target in TARGETS:
            copy = target / skill.name
            src, dst = files(skill), files(copy) if copy.is_dir() else set()
            problems += [f"{copy / f}: missing" for f in src - dst]
            problems += [f"{copy / f}: not in canonical" for f in dst - src]
            problems += [f"{copy / f}: differs" for f in src & dst if not filecmp.cmp(skill / f, copy / f, False)]
    return problems


def sync() -> None:
    for skill in (p for p in CANONICAL.iterdir() if p.is_dir()):
        for target in TARGETS:
            copy = target / skill.name
            if copy.exists():
                shutil.rmtree(copy)  # generated folder; the canonical copy is the source of truth
            shutil.copytree(skill, copy)
            print(f"synced {skill.name} -> {copy.relative_to(ROOT)}")


if __name__ == "__main__":
    if "--check" in sys.argv:
        found = drift()
        print("\n".join(found) or "skill adapters in sync")
        sys.exit(1 if found else 0)
    sync()
