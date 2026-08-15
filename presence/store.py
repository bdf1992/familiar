from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Callable


class PresenceError(ValueError):
    pass


def _identity_digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + sha256(encoded).hexdigest()


@dataclass(frozen=True)
class PresenceRecord:
    target_ref: str
    context_id: str
    established_by: str
    lifetime: str
    identity_digest: str
    status: str = "present"


class PresenceStore:
    """Host-owned bounded Presence. v0.5 intentionally supports session lifetime only."""

    def __init__(self, resolver: Callable[[str], Any | None]):
        self._resolver = resolver
        self._records: dict[tuple[str, str], PresenceRecord] = {}

    def lookup(self, target_ref: str) -> Any | None:
        value = self._resolver(target_ref)
        return deepcopy(value) if value is not None else None

    def exists(self, target_ref: str) -> bool:
        return self.lookup(target_ref) is not None

    def present(self, target_ref: str, context_id: str) -> bool:
        return (target_ref, context_id) in self._records

    def establish(self, target_ref: str, context_id: str, *, lifetime: str, cast_id: str) -> PresenceRecord:
        if lifetime != "session":
            raise PresenceError("v0.5 supports session Presence only")
        target = self.lookup(target_ref)
        if target is None:
            raise PresenceError(f"target does not exist: {target_ref}")
        record = PresenceRecord(
            target_ref=target_ref,
            context_id=context_id,
            established_by=cast_id,
            lifetime=lifetime,
            identity_digest=_identity_digest(target),
        )
        self._records[(target_ref, context_id)] = record
        return record

    def resolve(self, target_ref: str, context_id: str) -> Any:
        record = self._records.get((target_ref, context_id))
        if record is None:
            raise PresenceError(f"target is not present: {target_ref} in {context_id}")
        target = self.lookup(target_ref)
        if target is None:
            raise PresenceError(f"present target no longer resolves: {target_ref}")
        if _identity_digest(target) != record.identity_digest:
            raise PresenceError(f"present target identity changed: {target_ref}")
        return target

    def release(self, target_ref: str, context_id: str) -> None:
        self._records.pop((target_ref, context_id), None)

    def release_context(self, context_id: str) -> None:
        for key in [key for key in self._records if key[1] == context_id]:
            del self._records[key]
