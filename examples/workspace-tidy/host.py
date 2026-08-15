from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from kernel.spell_kernel import SpellKernel

SUFFIX = ".agentspells-disposable"


def snapshot(workspace: Path) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for path in sorted(workspace.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        rel = path.relative_to(workspace).as_posix()
        result[rel] = {
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "disposable": path.name.endswith(SUFFIX),
        }
    return result


class WorkspaceTidyHost:
    """Example host binding. Not part of the portable SPELL format."""

    def __init__(self, workspace: Path):
        self.workspace = workspace.resolve()
        self.before = snapshot(self.workspace)
        self.script = Path(__file__).parent / "scripts" / "tidy.py"
        self.executor_calls = 0

    def observe_workspace(self, phase: str, context: dict[str, Any]) -> dict[str, Any]:
        return {
            "value": snapshot(self.workspace),
            "source": "filesystem",
            "freshness_ms": 0,
        }

    def target_observable(self, phase: str, context: dict[str, Any]) -> bool:
        return self.workspace.is_dir()

    def disposable_absent(self, phase: str, context: dict[str, Any]) -> bool:
        return all(not item["disposable"] for item in snapshot(self.workspace).values())

    def preserve_unmarked(self, phase: str, context: dict[str, Any]) -> bool:
        if phase == "before":
            return True
        current = snapshot(self.workspace)
        for rel, original in self.before.items():
            if original["disposable"]:
                continue
            if rel not in current or current[rel]["sha256"] != original["sha256"]:
                return False
        return True

    @staticmethod
    def resolve_authority(caster: dict[str, Any], authority: str, context: dict[str, Any]) -> bool:
        return authority in set(caster.get("authority", []))

    def execute(self, spell: dict[str, Any], effect_id: str, context: dict[str, Any]) -> dict[str, Any]:
        self.executor_calls += 1
        completed = subprocess.run(
            [sys.executable, str(self.script), str(self.workspace)],
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(completed.stdout)

    def kernel(self) -> SpellKernel:
        return SpellKernel(
            observers={"workspace-state": self.observe_workspace},
            requirements={
                "target-observable": self.target_observable,
                "disposable-absent": self.disposable_absent,
            },
            limits={"preserve-unmarked": self.preserve_unmarked},
            authority_resolver=self.resolve_authority,
            executor=self.execute,
        )
