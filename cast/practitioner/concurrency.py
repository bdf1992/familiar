"""Concurrent Cast isolation and conflict semantics.

The casting model is clearest for sequential mutation. Two Practitioners or
sub-agents may resolve overlapping targets, close against the same pre-state,
then execute concurrently and invalidate one another's assumptions. Without an
explicit contract, closure evidence goes stale between admission and commit and
overlapping Casts produce lost updates.

The contract is expressed in terms of **observed pre-state identity** rather
than one universal locking strategy, because an Environment that can lock and
an Environment that can only compare-and-swap both need to be conforming.

```text
reservation   exclusive or shared acquisition before closure
optimistic    execute against isolated state, validate versions at commit
conflict      another consequence invalidated an assumption this Cast required
retry         a NEW attempt with fresh evidence, never a resumed old closure
```

The last one is the point. A conflict does not entitle a Cast to try its old
closure again: the closure was against a pre-state that no longer exists. A
retry is a new attempt, and its CAST is new evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any, Iterable, Mapping, Sequence

COMMITTED = "committed"
CONFLICT = "conflict"

SHARED = "shared"
EXCLUSIVE = "exclusive"


class ConcurrencyError(ValueError):
    """A reservation or commit could not be expressed."""


def version_of(value: Any) -> str:
    """A content-derived version token for observed state."""
    encoded = repr(value).encode("utf-8")
    return "sha256:" + sha256(encoded).hexdigest()


@dataclass(frozen=True)
class StateVersion:
    """The identity and version of one resource a Cast depends on.

    This is the material a CastPlan must retain for conflict detection. A
    resource name alone cannot detect anything: two Casts naming the same
    resource are only in conflict if the version they each observed differs
    from what is there at commit.
    """

    resource: str
    version: str

    def __post_init__(self) -> None:
        for name in ("resource", "version"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                raise ConcurrencyError(f"a state version requires {name}")


@dataclass(frozen=True)
class ConflictFinding:
    resource: str
    observed: str
    current: str

    def as_dict(self) -> dict[str, str]:
        return {"resource": self.resource, "observed": self.observed, "current": self.current}


@dataclass(frozen=True)
class CommitResult:
    status: str
    attempt_id: str
    conflicts: tuple[ConflictFinding, ...] = ()

    @property
    def committed(self) -> bool:
        return self.status == COMMITTED

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "attempt_id": self.attempt_id,
            "conflicts": [item.as_dict() for item in self.conflicts],
        }


@dataclass(frozen=True)
class CastAttempt:
    """One closure against one observed pre-state.

    A new attempt id per try is deliberate: retrying is a new attempt with
    fresh evidence, never a resumed closure against a pre-state that has since
    changed.
    """

    attempt_id: str
    observed: tuple[StateVersion, ...]

    def resources(self) -> tuple[str, ...]:
        return tuple(item.resource for item in self.observed)


class VersionedStore:
    """Reference optimistic-concurrency store.

    Reads hand out the current version. Commit validates every version the
    attempt observed and applies **all or nothing** -- a partial apply would be
    the lost update this exists to prevent, wearing a different name.
    """

    def __init__(self, initial: Mapping[str, Any] | None = None):
        self._values: dict[str, Any] = dict(initial or {})
        self._versions: dict[str, str] = {
            key: version_of(value) for key, value in self._values.items()
        }

    def read(self, resource: str) -> tuple[Any, StateVersion]:
        if resource not in self._values:
            raise ConcurrencyError(f"unknown resource: {resource}")
        return self._values[resource], StateVersion(resource, self._versions[resource])

    def value(self, resource: str) -> Any:
        return self._values[resource]

    def observe(self, *resources: str) -> tuple[StateVersion, ...]:
        return tuple(self.read(resource)[1] for resource in resources)

    def commit(self, attempt: CastAttempt, changes: Mapping[str, Any]) -> CommitResult:
        unknown = [key for key in changes if key not in self._values]
        if unknown:
            raise ConcurrencyError(f"unknown resource: {sorted(unknown)[0]}")

        conflicts = [
            ConflictFinding(item.resource, item.version, self._versions[item.resource])
            for item in attempt.observed
            if self._versions.get(item.resource) != item.version
        ]
        if conflicts:
            return CommitResult(CONFLICT, attempt.attempt_id, tuple(conflicts))

        for key, value in changes.items():
            self._values[key] = value
            self._versions[key] = version_of(value)
        return CommitResult(COMMITTED, attempt.attempt_id)


class ReservationLedger:
    """Reference pessimistic strategy with deterministic acquisition order.

    **Deadlock avoidance is by total order, not by timeout.** Every acquisition
    sorts its resources by name and takes them in that order, so two holders can
    never each hold what the other needs next. A timeout would turn a deadlock
    into a slow deadlock; ordering removes the cycle.
    """

    def __init__(self):
        self._held: dict[str, tuple[str, str]] = {}  # resource -> (holder, mode)
        self._shared: dict[str, set[str]] = {}

    def held_by(self, resource: str) -> str | None:
        entry = self._held.get(resource)
        return entry[0] if entry else None

    @staticmethod
    def acquisition_order(resources: Iterable[str]) -> tuple[str, ...]:
        """The total order every holder must follow."""
        return tuple(sorted(set(resources)))

    def acquire(self, holder: str, resources: Sequence[str], mode: str = EXCLUSIVE) -> bool:
        if mode not in (SHARED, EXCLUSIVE):
            raise ConcurrencyError(f"unknown reservation mode: {mode}")
        ordered = self.acquisition_order(resources)

        # Check the whole set before taking any of it, so a refusal leaves no
        # partial hold for another holder to wait behind.
        for resource in ordered:
            entry = self._held.get(resource)
            if entry is None:
                continue
            current_holder, current_mode = entry
            if current_holder == holder:
                continue
            if not (mode == SHARED and current_mode == SHARED):
                return False

        for resource in ordered:
            if mode == SHARED:
                self._shared.setdefault(resource, set()).add(holder)
                self._held[resource] = (holder, SHARED)
            else:
                self._held[resource] = (holder, EXCLUSIVE)
        return True

    def release(self, holder: str, resources: Sequence[str]) -> None:
        for resource in self.acquisition_order(resources):
            entry = self._held.get(resource)
            if entry is None:
                continue
            if entry[1] == SHARED:
                holders = self._shared.get(resource, set())
                holders.discard(holder)
                if holders:
                    self._held[resource] = (next(iter(holders)), SHARED)
                    continue
                self._shared.pop(resource, None)
                self._held.pop(resource, None)
            elif entry[0] == holder:
                self._held.pop(resource, None)


def replan(store: VersionedStore, attempt: CastAttempt, attempt_id: str) -> CastAttempt:
    """Produce a NEW attempt against current state after a conflict.

    Not a resumption. The previous closure was against a pre-state that no
    longer exists, so it cannot be retried -- only replaced.
    """
    if attempt_id == attempt.attempt_id:
        raise ConcurrencyError("a retry requires a new attempt id; a conflict is not resumable")
    return CastAttempt(attempt_id, store.observe(*attempt.resources()))
