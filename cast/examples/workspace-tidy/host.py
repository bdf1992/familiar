from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from environment.authority import RecordingHostCredential, attenuated_credential_enforcer
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

    def __init__(self, workspace: Path, *, write_authorized_casters: set[str] | None = None):
        self.workspace = workspace.resolve()
        self.script = Path(__file__).parent / "scripts" / "tidy.py"
        self.executor_calls = 0
        self.write_authorized_casters = set(write_authorized_casters or set())

    def observe_workspace(self, phase: str, context: dict[str, Any]) -> dict[str, Any]:
        return {
            "value": snapshot(self.workspace),
            "source": "filesystem",
            "freshness_ms": 0,
        }

    def target_observable(self, phase: str, context: dict[str, Any]) -> bool:
        return self.workspace.is_dir()

    def disposable_absent(self, phase: str, context: dict[str, Any]) -> bool:
        after = ((context.get("telemetry_after") or {}).get("workspace-state") or {}).get("value")
        if not isinstance(after, dict):
            return False
        return all(not item.get("disposable", False) for item in after.values())

    def preserve_unmarked(self, phase: str, context: dict[str, Any]) -> bool:
        before = ((context.get("telemetry") or {}).get("workspace-state") or {}).get("value")
        if not isinstance(before, dict):
            return False
        after = ((context.get("telemetry_after") or {}).get("workspace-state") or {}).get("value")
        if not isinstance(after, dict):
            return False
        for rel, original in before.items():
            if original.get("disposable", False):
                continue
            if rel not in after or after[rel].get("sha256") != original.get("sha256"):
                return False
        return True

    def resolve_authority(self, caster: dict[str, Any], authority: str, context: dict[str, Any]) -> bool:
        return authority == "workspace.write" and caster.get("id") in self.write_authorized_casters

    def execute(
        self,
        spell: dict[str, Any],
        effect_id: str,
        context: dict[str, Any],
        execution_max_ms: int | None,
    ) -> dict[str, Any]:
        self.executor_calls += 1
        completed = subprocess.run(
            [sys.executable, str(self.script), str(self.workspace)],
            check=True,
            capture_output=True,
            text=True,
            timeout=(execution_max_ms / 1000) if execution_max_ms is not None else None,
        )
        return json.loads(completed.stdout)

    def kernel(self) -> SpellKernel:
        return SpellKernel(
            observers={"workspace-state": self.observe_workspace},
            requirements={
                "target-observable": self.target_observable,
                "disposable-absent": self.disposable_absent,
                "preserve-unmarked": self.preserve_unmarked,
            },
            authority_resolver=self.resolve_authority,
            authority_enforcer=attenuated_credential_enforcer(RecordingHostCredential()),
            executor=self.execute,
        )
