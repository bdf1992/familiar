from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Callable


class MagicRuntimeError(ValueError):
    pass


@dataclass(frozen=True)
class MagicLimits:
    total_mana: int
    max_network: int
    max_local: int
    max_personal: int
    max_cast: int
    max_committed: int
    max_restored: int
    max_level: int
    drain_rate: int = 1

    def validate(self) -> None:
        values = asdict(self)
        if any(not isinstance(value, int) or value < 0 for value in values.values()):
            raise MagicRuntimeError("magic limits must be non-negative integers")
        if self.total_mana <= 0:
            raise MagicRuntimeError("total_mana must be positive")
        if self.max_network > self.total_mana:
            raise MagicRuntimeError("max_network cannot exceed total_mana")
        if self.max_local > self.max_network:
            raise MagicRuntimeError("max_local cannot exceed max_network")
        if self.max_personal > self.max_local:
            raise MagicRuntimeError("max_personal cannot exceed max_local")
        if self.max_cast > self.max_personal:
            raise MagicRuntimeError("max_cast cannot exceed max_personal")
        if self.max_committed > self.max_network:
            raise MagicRuntimeError("max_committed cannot exceed max_network")
        if self.max_restored > self.total_mana:
            raise MagicRuntimeError("max_restored cannot exceed total_mana")


@dataclass(frozen=True)
class MaintenanceEvidence:
    source_kind: str
    source_id: str
    domain: str
    mechanism: str
    before: Any
    after: Any
    observer: str

    def validate(self) -> None:
        if self.source_kind not in {"skill", "cast"}:
            raise MagicRuntimeError("maintenance source_kind must be skill or cast")
        for name in ("source_id", "domain", "mechanism", "observer"):
            if not getattr(self, name):
                raise MagicRuntimeError(f"maintenance evidence requires {name}")


@dataclass(frozen=True)
class ManaEvent:
    sequence: int
    operation: str
    actor: str | None
    locality: str | None
    amount: int
    details: dict[str, Any]
    previous_digest: str | None
    digest: str


@dataclass
class _State:
    limits: MagicLimits
    ambient: dict[str, int] = field(default_factory=dict)
    claimed: dict[tuple[str, str], int] = field(default_factory=dict)
    committed: dict[str, dict[str, Any]] = field(default_factory=dict)
    spent: dict[str, int] = field(default_factory=dict)


RoleResolver = Callable[[str, str, str], bool]
MaintenanceVerifier = Callable[[MaintenanceEvidence], int]


class MagicRuntime:
    """Conserved shared Mana carried by the Environment.

    The runtime owns legal Mana transitions and maintained limits. It does not
    define Spell level semantics; max_level is only an admission setting until
    a later Spell/level specification gives it portable meaning.
    """

    ROLE_DOMAINS_MAINTAINER = "domains-maintainer"

    def __init__(
        self,
        limits: MagicLimits,
        *,
        initial_locality: str = "network",
        path: str | Path | None = None,
        role_resolver: RoleResolver | None = None,
        maintenance_verifier: MaintenanceVerifier | None = None,
    ):
        limits.validate()
        self._path = Path(path) if path is not None else None
        self._role_resolver = role_resolver
        self._maintenance_verifier = maintenance_verifier
        self._events: list[ManaEvent] = []
        self._state = _State(limits=limits)

        if self._path is not None and self._path.exists():
            self._load()
            if self._state.limits.total_mana != limits.total_mana:
                raise MagicRuntimeError("persisted total_mana does not match requested network")
        else:
            self._append(
                "genesis",
                actor=None,
                locality=initial_locality,
                amount=limits.total_mana,
                details={"limits": asdict(limits)},
                persist=False,
            )
            self._persist()

    @property
    def limits(self) -> MagicLimits:
        return self._state.limits

    @property
    def events(self) -> tuple[ManaEvent, ...]:
        return tuple(self._events)

    def sense(self, locality: str, *, subject: str | None = None) -> dict[str, int]:
        result = {
            "ambient": self._state.ambient.get(locality, 0),
            "claimed": sum(
                amount for (place, _actor), amount in self._state.claimed.items() if place == locality
            ),
        }
        if subject is not None:
            result["subject_claimed"] = self.claimed_by(subject, locality=locality)
        return result

    def claimed_by(self, actor: str, *, locality: str | None = None) -> int:
        return sum(
            amount
            for (place, holder), amount in self._state.claimed.items()
            if holder == actor and (locality is None or place == locality)
        )

    def committed_by(self, actor: str) -> int:
        return sum(item["amount"] for item in self._state.committed.values() if item["actor"] == actor)

    def total(self) -> int:
        return self._accounted_total()

    def claim(self, actor: str, locality: str, amount: int) -> ManaEvent:
        self._positive(amount)
        if self._state.ambient.get(locality, 0) < amount:
            raise MagicRuntimeError("insufficient ambient Mana")
        if self._network_active() + amount > self.limits.max_network:
            raise MagicRuntimeError("max_network exceeded")
        if self._local_active(locality) + amount > self.limits.max_local:
            raise MagicRuntimeError("max_local exceeded")
        if self._personal_active(actor) + amount > self.limits.max_personal:
            raise MagicRuntimeError("max_personal exceeded")
        return self._append("claim", actor=actor, locality=locality, amount=amount, details={})

    def release(self, actor: str, locality: str, amount: int) -> ManaEvent:
        self._positive(amount)
        if self._state.claimed.get((locality, actor), 0) < amount:
            raise MagicRuntimeError("insufficient claimed Mana")
        return self._append("release", actor=actor, locality=locality, amount=amount, details={})

    def drain(self, *, ticks: int = 1, locality: str | None = None) -> tuple[ManaEvent, ...]:
        self._positive(ticks)
        if self.limits.drain_rate == 0:
            return ()
        events: list[ManaEvent] = []
        for (place, actor), claimed in sorted(list(self._state.claimed.items())):
            if locality is not None and place != locality:
                continue
            amount = min(claimed, self.limits.drain_rate * ticks)
            if amount:
                events.append(self._append("drain", actor=actor, locality=place, amount=amount, details={"ticks": ticks}))
        return tuple(events)

    def commit(self, cast_id: str, actor: str, locality: str, amount: int, *, level: int | None = None) -> ManaEvent:
        self._positive(amount)
        if cast_id in self._state.committed:
            raise MagicRuntimeError(f"cast already has committed Mana: {cast_id}")
        if level is not None:
            self.admit_level(level)
        if amount > self.limits.max_cast:
            raise MagicRuntimeError("max_cast exceeded")
        if self._committed_total() + amount > self.limits.max_committed:
            raise MagicRuntimeError("max_committed exceeded")
        if self._state.claimed.get((locality, actor), 0) < amount:
            raise MagicRuntimeError("insufficient claimed Mana")
        return self._append(
            "commit",
            actor=actor,
            locality=locality,
            amount=amount,
            details={"cast_id": cast_id, "level": level},
        )

    def settle(self, cast_id: str, *, spent: int) -> ManaEvent:
        if not isinstance(spent, int) or spent < 0:
            raise MagicRuntimeError("spent must be a non-negative integer")
        commitment = self._state.committed.get(cast_id)
        if commitment is None:
            raise MagicRuntimeError(f"unknown Mana commitment: {cast_id}")
        if spent > commitment["amount"]:
            raise MagicRuntimeError("cannot spend more Mana than committed")
        return self._append(
            "settle",
            actor=commitment["actor"],
            locality=commitment["locality"],
            amount=commitment["amount"],
            details={"cast_id": cast_id, "spent": spent, "released": commitment["amount"] - spent},
        )

    def restore(self, actor: str, locality: str, evidence: MaintenanceEvidence) -> ManaEvent:
        evidence.validate()
        self._require_maintainer(actor, evidence.domain)
        if self._maintenance_verifier is None:
            raise MagicRuntimeError("maintenance verifier unavailable")
        confirmed = self._maintenance_verifier(evidence)
        if not isinstance(confirmed, int) or confirmed < 0:
            raise MagicRuntimeError("maintenance verifier returned invalid restoration amount")
        if confirmed == 0:
            raise MagicRuntimeError("maintenance did not confirm a restoration")
        amount = min(confirmed, self.limits.max_restored, self._state.spent.get(locality, 0))
        if amount <= 0:
            raise MagicRuntimeError("no eligible spent Mana can be restored")
        return self._append(
            "restore",
            actor=actor,
            locality=locality,
            amount=amount,
            details={"role": self.ROLE_DOMAINS_MAINTAINER, "evidence": asdict(evidence), "confirmed": confirmed},
        )

    def configure(self, actor: str, changes: dict[str, int], evidence: MaintenanceEvidence) -> ManaEvent:
        evidence.validate()
        self._require_maintainer(actor, evidence.domain)
        if evidence.domain != "environment":
            raise MagicRuntimeError("magic runtime settings are Environment mechanisms")
        if self._maintenance_verifier is None:
            raise MagicRuntimeError("maintenance verifier unavailable")
        confirmed = self._maintenance_verifier(evidence)
        if confirmed <= 0:
            raise MagicRuntimeError("configuration maintenance was not independently confirmed")
        if "total_mana" in changes:
            raise MagicRuntimeError("total_mana is conserved and cannot be reconfigured")
        unknown = set(changes) - set(asdict(self.limits))
        if unknown:
            raise MagicRuntimeError(f"unknown magic setting: {sorted(unknown)[0]}")
        candidate_data = asdict(self.limits)
        candidate_data.update(changes)
        candidate = MagicLimits(**candidate_data)
        candidate.validate()
        self._validate_limits_against_live_state(candidate)
        return self._append(
            "configure",
            actor=actor,
            locality=None,
            amount=0,
            details={"changes": changes, "evidence": asdict(evidence)},
        )

    def admit_level(self, level: int) -> None:
        if not isinstance(level, int) or level < 0:
            raise MagicRuntimeError("level must be a non-negative integer")
        if level > self.limits.max_level:
            raise MagicRuntimeError("max_level exceeded")

    def _require_maintainer(self, actor: str, domain: str) -> None:
        if self._role_resolver is None or not self._role_resolver(actor, self.ROLE_DOMAINS_MAINTAINER, domain):
            raise MagicRuntimeError("Domains Maintainer role unavailable for domain")

    def _append(
        self,
        operation: str,
        *,
        actor: str | None,
        locality: str | None,
        amount: int,
        details: dict[str, Any],
        persist: bool = True,
    ) -> ManaEvent:
        sequence = len(self._events)
        previous_digest = self._events[-1].digest if self._events else None
        material = {
            "sequence": sequence,
            "operation": operation,
            "actor": actor,
            "locality": locality,
            "amount": amount,
            "details": details,
            "previous_digest": previous_digest,
        }
        digest = self._event_digest(material)
        event = ManaEvent(digest=digest, **material)
        self._apply(event)
        self._events.append(event)
        self._validate_state()
        if persist:
            self._persist()
        return event

    def _apply(self, event: ManaEvent) -> None:
        operation = event.operation
        locality = event.locality
        actor = event.actor
        amount = event.amount
        if operation == "genesis":
            limits = MagicLimits(**event.details["limits"])
            limits.validate()
            self._state = _State(limits=limits, ambient={str(locality): amount})
        elif operation == "claim":
            self._move_ambient(locality, -amount)
            self._move_claim(locality, actor, amount)
        elif operation in {"release", "drain"}:
            self._move_claim(locality, actor, -amount)
            self._move_ambient(locality, amount)
        elif operation == "commit":
            cast_id = event.details["cast_id"]
            self._move_claim(locality, actor, -amount)
            self._state.committed[cast_id] = {"actor": actor, "locality": locality, "amount": amount}
        elif operation == "settle":
            cast_id = event.details["cast_id"]
            commitment = self._state.committed.pop(cast_id)
            spent = event.details["spent"]
            released = event.details["released"]
            if spent:
                self._state.spent[str(locality)] = self._state.spent.get(str(locality), 0) + spent
            if released:
                self._move_claim(locality, actor, released)
            if commitment["amount"] != spent + released:
                raise MagicRuntimeError("invalid settlement")
        elif operation == "restore":
            current = self._state.spent.get(str(locality), 0)
            if current < amount:
                raise MagicRuntimeError("restore exceeds spent Mana")
            self._state.spent[str(locality)] = current - amount
            self._prune(self._state.spent, str(locality))
            self._move_ambient(locality, amount)
        elif operation == "configure":
            data = asdict(self._state.limits)
            data.update(event.details["changes"])
            self._state.limits = MagicLimits(**data)
            self._state.limits.validate()
        else:
            raise MagicRuntimeError(f"unknown Mana event operation: {operation}")

    def _move_ambient(self, locality: str | None, delta: int) -> None:
        key = str(locality)
        next_value = self._state.ambient.get(key, 0) + delta
        if next_value < 0:
            raise MagicRuntimeError("ambient Mana cannot be negative")
        self._state.ambient[key] = next_value
        self._prune(self._state.ambient, key)

    def _move_claim(self, locality: str | None, actor: str | None, delta: int) -> None:
        key = (str(locality), str(actor))
        next_value = self._state.claimed.get(key, 0) + delta
        if next_value < 0:
            raise MagicRuntimeError("claimed Mana cannot be negative")
        self._state.claimed[key] = next_value
        self._prune(self._state.claimed, key)

    def _validate_state(self) -> None:
        if self._accounted_total() != self.limits.total_mana:
            raise MagicRuntimeError("Mana conservation violated")
        if self._network_active() > self.limits.max_network:
            raise MagicRuntimeError("live state exceeds max_network")
        if self._committed_total() > self.limits.max_committed:
            raise MagicRuntimeError("live state exceeds max_committed")
        for locality in set(self._state.ambient) | {place for place, _ in self._state.claimed}:
            if self._local_active(locality) > self.limits.max_local:
                raise MagicRuntimeError("live state exceeds max_local")
        actors = {actor for _, actor in self._state.claimed} | {item["actor"] for item in self._state.committed.values()}
        for actor in actors:
            if self._personal_active(actor) > self.limits.max_personal:
                raise MagicRuntimeError("live state exceeds max_personal")
        for item in self._state.committed.values():
            if item["amount"] > self.limits.max_cast:
                raise MagicRuntimeError("live commitment exceeds max_cast")

    def _validate_limits_against_live_state(self, candidate: MagicLimits) -> None:
        current = self._state.limits
        self._state.limits = candidate
        try:
            self._validate_state()
        finally:
            self._state.limits = current

    def _accounted_total(self) -> int:
        return (
            sum(self._state.ambient.values())
            + sum(self._state.claimed.values())
            + self._committed_total()
            + sum(self._state.spent.values())
        )

    def _committed_total(self) -> int:
        return sum(item["amount"] for item in self._state.committed.values())

    def _network_active(self) -> int:
        return sum(self._state.claimed.values()) + self._committed_total()

    def _local_active(self, locality: str) -> int:
        claimed = sum(amount for (place, _), amount in self._state.claimed.items() if place == locality)
        committed = sum(item["amount"] for item in self._state.committed.values() if item["locality"] == locality)
        return claimed + committed

    def _personal_active(self, actor: str) -> int:
        return self.claimed_by(actor) + self.committed_by(actor)

    def _persist(self) -> None:
        if self._path is None:
            return
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"magic_runtime": "0.6-draft", "events": [asdict(event) for event in self._events]}
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        fd, temporary = tempfile.mkstemp(prefix=self._path.name + ".", dir=str(self._path.parent), text=True)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self._path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def _load(self) -> None:
        with self._path.open("r", encoding="utf-8") as handle:  # type: ignore[union-attr]
            payload = json.load(handle)
        if payload.get("magic_runtime") != "0.6-draft":
            raise MagicRuntimeError("unsupported persisted magic runtime")
        raw_events = payload.get("events")
        if not isinstance(raw_events, list) or not raw_events:
            raise MagicRuntimeError("magic ledger is empty")
        self._events = []
        for raw in raw_events:
            expected_previous = self._events[-1].digest if self._events else None
            material = {
                "sequence": raw["sequence"],
                "operation": raw["operation"],
                "actor": raw.get("actor"),
                "locality": raw.get("locality"),
                "amount": raw["amount"],
                "details": raw.get("details") or {},
                "previous_digest": raw.get("previous_digest"),
            }
            if material["sequence"] != len(self._events):
                raise MagicRuntimeError("magic ledger sequence is invalid")
            if material["previous_digest"] != expected_previous:
                raise MagicRuntimeError("magic ledger chain is broken")
            digest = self._event_digest(material)
            if raw.get("digest") != digest:
                raise MagicRuntimeError("magic ledger event digest mismatch")
            event = ManaEvent(digest=digest, **material)
            self._apply(event)
            self._events.append(event)
            self._validate_state()

    @staticmethod
    def _event_digest(material: dict[str, Any]) -> str:
        encoded = json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        return "sha256:" + sha256(encoded).hexdigest()

    @staticmethod
    def _positive(value: int) -> None:
        if not isinstance(value, int) or value <= 0:
            raise MagicRuntimeError("amount must be a positive integer")

    @staticmethod
    def _prune(mapping: dict[Any, int], key: Any) -> None:
        if mapping.get(key) == 0:
            mapping.pop(key, None)
