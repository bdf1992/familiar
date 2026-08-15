"""Persistent Familiar registry.

The registry owns deterministic identity continuity. Models may propose Familiar
changes, but the store refuses stale writes and unauthorized holder/form
replacement.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any


class FamiliarRegistryError(RuntimeError):
    pass


class FamiliarNotFound(FamiliarRegistryError):
    pass


class FamiliarConflict(FamiliarRegistryError):
    def __init__(self, current_revision: str):
        super().__init__("stale Familiar revision; reload and reapply the change")
        self.current_revision = current_revision


class FamiliarIdentityChangeForbidden(FamiliarRegistryError):
    pass


def canonical_bytes(record: dict[str, Any]) -> bytes:
    return json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def revision_of(record: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_bytes(record)).hexdigest()[:16]


class FileFamiliarRegistry:
    """A local-first atomic Familiar store inside one authorized directory."""

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, familiar_id: str) -> Path:
        if not familiar_id or familiar_id in {".", ".."} or "/" in familiar_id or "\\" in familiar_id:
            raise ValueError("familiar_id must be a simple stable id")
        return self.root / f"{familiar_id}.json"

    def load(self, familiar_id: str) -> tuple[dict[str, Any], str]:
        path = self._path(familiar_id)
        if not path.exists():
            raise FamiliarNotFound(familiar_id)
        with path.open("r", encoding="utf-8") as handle:
            record = json.load(handle)
        return record, revision_of(record)

    def save(
        self,
        record: dict[str, Any],
        *,
        expected_revision: str | None = None,
        identity_change_authorized: bool = False,
    ) -> str:
        familiar_id = str(record.get("id") or "")
        path = self._path(familiar_id)

        if path.exists():
            current, current_revision = self.load(familiar_id)
            if expected_revision is None or expected_revision != current_revision:
                raise FamiliarConflict(current_revision)

            holder_changed = current.get("holder") != record.get("holder")
            form_changed = current.get("form") != record.get("form")
            if (holder_changed or form_changed) and not identity_change_authorized:
                raise FamiliarIdentityChangeForbidden(
                    "holder or form replacement requires explicit holder-authorized identity change"
                )
        elif expected_revision is not None:
            raise FamiliarConflict("absent")

        # Copy so callers cannot mutate the value being serialized mid-save.
        stable_record = deepcopy(record)
        payload = json.dumps(stable_record, indent=2, ensure_ascii=False, sort_keys=True) + "\n"

        fd, tmp_name = tempfile.mkstemp(prefix=f".{familiar_id}.", suffix=".tmp", dir=self.root)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, path)
        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)

        return revision_of(stable_record)
