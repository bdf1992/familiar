from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
from typing import Any

from .validation import validate_familiar


class FamiliarStoreError(ValueError):
    pass


def _digest(value: dict[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + sha256(encoded).hexdigest()


def _file_key(familiar_id: str) -> str:
    return sha256(familiar_id.encode("utf-8")).hexdigest() + ".json"


def _atomic_json_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.parent.chmod(0o700)
    except OSError:
        pass
    fd, tmp_name = tempfile.mkstemp(prefix=".tmp-", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, sort_keys=True, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.chmod(tmp_name, 0o600)
        except OSError:
            pass
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


@dataclass(frozen=True)
class FamiliarRef:
    id: str
    caster_id: str
    revision: int
    digest: str


class FamiliarStore:
    """Exact caster-owned Familiar persistence. It grants no runtime authority.

    With no root path the store remains process-local for tests and ephemeral
    hosts. Supplying a root enables restart-safe local persistence. Files use
    content-derived names so Familiar ids never become filesystem paths.
    """

    def __init__(self, root: str | Path | None = None):
        self._values: dict[str, tuple[int, dict[str, Any]]] = {}
        self.root = Path(root).expanduser().resolve() if root is not None else None
        if self.root is not None:
            self.root.mkdir(parents=True, exist_ok=True)
            try:
                self.root.chmod(0o700)
            except OSError:
                pass

    def _path(self, familiar_id: str) -> Path:
        if self.root is None:
            raise FamiliarStoreError("store has no persistent root")
        return self.root / _file_key(familiar_id)

    def _read(self, familiar_id: str) -> tuple[int, dict[str, Any]] | None:
        if self.root is None:
            return self._values.get(familiar_id)
        path = self._path(familiar_id)
        if not path.exists():
            return None
        try:
            envelope = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise FamiliarStoreError(f"cannot read Familiar store entry: {familiar_id}") from exc
        if envelope.get("id") != familiar_id:
            raise FamiliarStoreError("stored Familiar id does not match lookup id")
        revision = envelope.get("revision")
        value = envelope.get("familiar")
        if not isinstance(revision, int) or revision < 1 or not isinstance(value, dict):
            raise FamiliarStoreError("stored Familiar envelope is invalid")
        validate_familiar(value)
        if envelope.get("digest") != _digest(value):
            raise FamiliarStoreError("stored Familiar digest does not match artifact")
        return revision, value

    def put(self, familiar: dict[str, Any], *, caster_id: str) -> FamiliarRef:
        validate_familiar(familiar)
        if familiar["caster"]["id"] != caster_id:
            raise FamiliarStoreError("Familiar caster does not match committing caster")
        current = self._read(familiar["id"])
        revision = 1 if current is None else current[0] + 1
        value = deepcopy(familiar)
        digest = _digest(value)
        if self.root is None:
            self._values[familiar["id"]] = (revision, value)
        else:
            _atomic_json_write(
                self._path(familiar["id"]),
                {"id": familiar["id"], "revision": revision, "digest": digest, "familiar": value},
            )
        return FamiliarRef(familiar["id"], caster_id, revision, digest)

    def resolve(self, ref: FamiliarRef) -> dict[str, Any]:
        current = self._read(ref.id)
        if current is None:
            raise FamiliarStoreError(f"Familiar not found: {ref.id}")
        revision, value = current
        if revision != ref.revision or _digest(value) != ref.digest:
            raise FamiliarStoreError("Familiar reference is stale or does not match stored artifact")
        if value["caster"]["id"] != ref.caster_id:
            raise FamiliarStoreError("Familiar ownership changed")
        return deepcopy(value)
