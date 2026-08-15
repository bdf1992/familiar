from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any

from kernel.spell_kernel import validate_familiar


class FamiliarStoreError(ValueError):
    pass


def _digest(value: dict[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + sha256(encoded).hexdigest()


@dataclass(frozen=True)
class FamiliarRef:
    id: str
    caster_id: str
    revision: int
    digest: str


class FamiliarStore:
    """Exact caster-owned Familiar persistence. It grants no runtime authority."""

    def __init__(self):
        self._values: dict[str, tuple[int, dict[str, Any]]] = {}

    def put(self, familiar: dict[str, Any], *, caster_id: str) -> FamiliarRef:
        validate_familiar(familiar)
        if familiar["caster"]["id"] != caster_id:
            raise FamiliarStoreError("Familiar caster does not match committing caster")
        current = self._values.get(familiar["id"])
        revision = 1 if current is None else current[0] + 1
        value = deepcopy(familiar)
        self._values[familiar["id"]] = (revision, value)
        return FamiliarRef(familiar["id"], caster_id, revision, _digest(value))

    def resolve(self, ref: FamiliarRef) -> dict[str, Any]:
        current = self._values.get(ref.id)
        if current is None:
            raise FamiliarStoreError(f"Familiar not found: {ref.id}")
        revision, value = current
        if revision != ref.revision or _digest(value) != ref.digest:
            raise FamiliarStoreError("Familiar reference is stale or does not match stored artifact")
        if value["caster"]["id"] != ref.caster_id:
            raise FamiliarStoreError("Familiar ownership changed")
        return deepcopy(value)
