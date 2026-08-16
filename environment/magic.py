from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Callable


DOMAINS = frozenset({"spell", "cast", "familiar", "registry", "environment"})


class MagicRuntimeError(ValueError):
    pass


def _is_int(value: Any) -> bool:
    """Python bool is an int subclass; runtime quantities deliberately are not."""
    return type(value) is int


@dataclass(frozen=True)
class MagicLimits:
    """Maintained runtime ceilings. The conserved quantity N is not a setting."""

    max_network: int
    max_local: int
    max_personal: int
    max_cast: int
    max_committed: int
    max_restored: int
    max_level: int
    drain_rate: int = 1

    def validate(self, *, total_mana: int) -> None:
        values = asdict(self)
        if any(not _is_int(value) or value < 0 for value in values.values()):
            raise MagicRuntimeError("magic limits must be non-negative integers")
        if not _is_int(total_mana) or total_mana <= 0:
            raise MagicRuntimeError("total_mana must be a positive integer")
        if self.max_network > total_mana:
            raise MagicRuntimeError("max_network cannot exceed total_mana")
        if self.max_local > self.max_network:
            raise MagicRuntimeError("max_local cannot exceed max_network")
        if self.max_personal > self.max_local:
            raise MagicRuntimeError("max_personal cannot exceed max_local")
        if self.max_cast > self.max_personal:
            raise MagicRuntimeError("max_cast cannot exceed max_personal")
        if self.max_committed > self.max_network:
            raise MagicRuntimeError("max_committed cannot exceed max_network")
        if self.max_restored > total_mana:
            raise MagicRuntimeError("max_restored cannot exceed total_mana")


@dataclass(frozen=True)
class MaintenanceEvidence:
    """Candidate evidence identifying one Maintenance Act.

    `before` and `after` are claims supplied to the Environment verifier. They
    do not certify themselves. The verifier supplies the accepted independent
    observer and receipt in MaintenanceDecision.
    """

    source_kind: str
    source_id: str
    domain: str
    mechanism: str
    before: dict[str, Any]
    after: dict[str, Any]

    def validate(self) -> None:
        if self.source_kind not in {"skill", "cast"}:
            raise MagicRuntimeError("maintenance source_kind must be skill or cast")
        if self.domain not in DOMAINS:
            raise MagicRuntimeError("maintenance domain must be one of the five repository domains")
        for name in ("source_id", "mechanism"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise MagicRuntimeError(f"maintenance evidence requires {name}")
        if not isinstance(self.before, dict) or not isinstance(self.after, dict):
            raise MagicRuntimeError("maintenance before/after observations must be mappings")

    @property
    def act_id(self) -> str:
        return f"{self.source_kind}:{self.domain}:{self.source_id}"

    @property
    def source_key(self) -> str:
        """One attributable execution source, independent of claimed domain.

        `act_id` carries the domain, so the same source rebound to another
        domain produces a different act. Source identity must be consumed on
        its own or a single execution can manufacture one maintenance
        consequence per domain it is willing to claim.
        """
        return f"{self.source_kind}:{self.source_id}"


@dataclass(frozen=True)
class MaintenanceDecision:
    """Environment decision about one candidate Maintenance Act."""

    confirmed: bool
    restorable: int = 0
    observer: str = ""
    receipt_id: str = ""
    reason: str = ""

    def validate(self) -> None:
        if type(self.confirmed) is not bool:
            raise MagicRuntimeError("maintenance decision confirmed must be boolean")
        if not _is_int(self.restorable) or self.restorable < 0:
            raise MagicRuntimeError("maintenance decision restorable must be a non-negative integer")
        if self.restorable and not self.confirmed:
            raise MagicRuntimeError("unconfirmed maintenance cannot restore Mana")
        if self.confirmed:
            for name in ("observer", "receipt_id"):
                value = getattr(self, name)
                if not isinstance(value, str) or not value:
                    raise MagicRuntimeError(f"confirmed maintenance requires {name}")


@dataclass(frozen=True)
class ConsequenceDecision:
    """Environment observation used to settle one committed Cast."""

    confirmed: bool
    spent: int = 0
    observer: str = ""
    receipt_id: str = ""
    reason: str = ""

    def validate(self) -> None:
        if type(self.confirmed) is not bool:
            raise MagicRuntimeError("consequence decision confirmed must be boolean")
        if not _is_int(self.spent) or self.spent < 0:
            raise MagicRuntimeError("consequence decision spent must be a non-negative integer")
        if self.spent and not self.confirmed:
            raise MagicRuntimeError("unconfirmed consequence cannot spend Mana")
        if self.confirmed:
            for name in ("observer", "receipt_id"):
                value = getattr(self, name)
                if not isinstance(value, str) or not value:
                    raise MagicRuntimeError(f"confirmed consequence requires {name}")


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


@dataclass(frozen=True)
class SpentLot:
    cast_id: str
    actor: str
    locality: str
    amount: int
    created_sequence: int


@dataclass
class _State:
    total_mana: int
    limits: MagicLimits
    ambient: dict[str, int] = field(default_factory=dict)
    claimed: dict[tuple[str, str], int] = field(default_factory=dict)
    committed: dict[str, dict[str, Any]] = field(default_factory=dict)
    spent: dict[str, SpentLot] = field(default_factory=dict)
    cast_ids: set[str] = field(default_factory=set)
    # Three independent replay guards. One Maintenance Act, one attributable
    # execution source, and one accepted verifier receipt each close at most
    # one maintenance consequence.
    maintenance_acts: set[str] = field(default_factory=set)
    maintenance_sources: set[str] = field(default_factory=set)
    maintenance_receipts: set[str] = field(default_factory=set)


AccessResolver = Callable[[str, str, str], bool]
RouteResolver = Callable[[str, str], bool]
RoleResolver = Callable[[str, str, str], bool]
MaintenanceVerifier = Callable[[MaintenanceEvidence], MaintenanceDecision]
ConsequenceVerifier = Callable[[str, dict[str, Any]], ConsequenceDecision]


class MagicRuntime:
    """Single-writer conserved Mana runtime carried by an Environment."""

    ROLE_DOMAINS_MAINTAINER = "domains-maintainer"
    SETTINGS_MECHANISM = "magic-runtime.settings"

    def __init__(
        self,
        total_mana: int,
        limits: MagicLimits,
        *,
        initial_locality: str = "network",
        path: str | Path | None = None,
        access_resolver: AccessResolver | None = None,
        route_resolver: RouteResolver | None = None,
        role_resolver: RoleResolver | None = None,
        maintenance_verifier: MaintenanceVerifier | None = None,
        consequence_verifier: ConsequenceVerifier | None = None,
    ):
        limits.validate(total_mana=total_mana)
        self._name(initial_locality, "initial_locality")
        self._path = Path(path) if path is not None else None
        self._access_resolver = access_resolver
        self._route_resolver = route_resolver
        self._role_resolver = role_resolver
        self._maintenance_verifier = maintenance_verifier
        self._consequence_verifier = consequence_verifier
        self._events: list[ManaEvent] = []
        self._state = _State(total_mana=total_mana, limits=limits)

        if self._path is not None and self._path.exists():
            self._load()
            if self._state.total_mana != total_mana:
                raise MagicRuntimeError("persisted total_mana does not match requested network")
        else:
            self._append(
                "genesis",
                actor=None,
                locality=initial_locality,
                amount=total_mana,
                details={"total_mana": total_mana, "limits": asdict(limits)},
                persist=False,
            )
            self._persist()

    @property
    def total_mana(self) -> int:
        return self._state.total_mana

    @property
    def limits(self) -> MagicLimits:
        return self._state.limits

    @property
    def events(self) -> tuple[ManaEvent, ...]:
        # Never expose references into the digest-bearing internal ledger.
        return tuple(deepcopy(self._events))

    def sense(self, observer: str, locality: str, *, subject: str | None = None) -> dict[str, int]:
        self._name(observer, "observer")
        self._name(locality, "locality")
        self._require_access(observer, "mana.sense", locality)
        result = {
            "ambient": self._state.ambient.get(locality, 0),
            "claimed": sum(amount for (place, _), amount in self._state.claimed.items() if place == locality),
        }
        if subject is not None:
            self._name(subject, "subject")
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

    def spent_total(self, *, locality: str | None = None) -> int:
        return sum(lot.amount for lot in self._state.spent.values() if locality is None or lot.locality == locality)

    def total(self) -> int:
        return self._accounted_total()

    def flow(self, source: str, target: str, amount: int) -> ManaEvent:
        self._name(source, "source locality")
        self._name(target, "target locality")
        self._positive(amount)
        if source == target:
            raise MagicRuntimeError("Mana flow requires distinct localities")
        if self._route_resolver is None or not self._route_resolver(source, target):
            raise MagicRuntimeError("Mana route unavailable")
        if self._state.ambient.get(source, 0) < amount:
            raise MagicRuntimeError("insufficient ambient Mana")
        return self._append("flow", actor=None, locality=source, amount=amount, details={"target": target})

    def claim(self, actor: str, locality: str, amount: int) -> ManaEvent:
        self._name(actor, "actor")
        self._name(locality, "locality")
        self._positive(amount)
        self._require_access(actor, "mana.claim", locality)
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
        self._name(actor, "actor")
        self._name(locality, "locality")
        self._positive(amount)
        self._require_access(actor, "mana.release", locality)
        if self._state.claimed.get((locality, actor), 0) < amount:
            raise MagicRuntimeError("insufficient claimed Mana")
        return self._append("release", actor=actor, locality=locality, amount=amount, details={})

    def drain(self, *, ticks: int = 1, locality: str | None = None) -> tuple[ManaEvent, ...]:
        self._positive(ticks)
        if locality is not None:
            self._name(locality, "locality")
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
        self._name(cast_id, "cast_id")
        self._name(actor, "actor")
        self._name(locality, "locality")
        self._positive(amount)
        self._require_access(actor, "mana.commit", locality)
        if cast_id in self._state.cast_ids:
            raise MagicRuntimeError(f"cast id already used for Mana: {cast_id}")
        if level is not None:
            self.admit_level(level)
        if amount > self.limits.max_cast:
            raise MagicRuntimeError("max_cast exceeded")
        if self._committed_total() + amount > self.limits.max_committed:
            raise MagicRuntimeError("max_committed exceeded")
        if self._state.claimed.get((locality, actor), 0) < amount:
            raise MagicRuntimeError("insufficient claimed Mana")
        return self._append(
            "commit", actor=actor, locality=locality, amount=amount, details={"cast_id": cast_id, "level": level}
        )

    def settle(self, cast_id: str) -> ManaEvent:
        """Settle a Cast only from an Environment-produced consequence decision."""
        self._name(cast_id, "cast_id")
        commitment = self._state.committed.get(cast_id)
        if commitment is None:
            raise MagicRuntimeError(f"unknown Mana commitment: {cast_id}")
        decision = self._verify_consequence(cast_id, commitment)
        if not decision.confirmed:
            raise MagicRuntimeError("Cast consequence has not been independently confirmed")
        if decision.observer == commitment["actor"]:
            raise MagicRuntimeError("Cast settlement requires an independent consequence observer")
        if decision.spent > commitment["amount"]:
            raise MagicRuntimeError("cannot spend more Mana than committed")
        return self._append(
            "settle",
            actor=commitment["actor"],
            locality=commitment["locality"],
            amount=commitment["amount"],
            details={
                "cast_id": cast_id,
                "spent": decision.spent,
                "released": commitment["amount"] - decision.spent,
                "decision": asdict(decision),
            },
        )

    def restore(self, actor: str, locality: str, evidence: MaintenanceEvidence) -> ManaEvent:
        """Record one confirmed Maintenance Act and any restoration it causes.

        A confirmed act is consumed even when zero Mana is currently restorable.
        Restoration is therefore a possible consequence of maintenance, not its
        definition and not a deferred credit that can be replayed later.
        """
        self._name(actor, "actor")
        self._name(locality, "locality")
        decision = self._verify_maintenance_act(actor, evidence)
        amount = min(decision.restorable, self.limits.max_restored, self.spent_total(locality=locality))
        allocations = self._restoration_allocations(locality, amount) if amount else []
        return self._append(
            "maintenance",
            actor=actor,
            locality=locality,
            amount=amount,
            details={
                "role": self.ROLE_DOMAINS_MAINTAINER,
                "act_id": evidence.act_id,
                "evidence": asdict(evidence),
                "decision": asdict(decision),
                "restored_from": allocations,
            },
        )

    def configure(self, actor: str, changes: dict[str, int], evidence: MaintenanceEvidence) -> ManaEvent:
        self._name(actor, "actor")
        if not isinstance(changes, dict):
            raise MagicRuntimeError("magic setting changes must be a mapping")
        evidence.validate()
        self._require_unapplied_act(evidence)
        self._require_maintainer(actor, evidence.domain)
        if evidence.domain != "environment" or evidence.mechanism != self.SETTINGS_MECHANISM:
            raise MagicRuntimeError("runtime settings require maintenance of magic-runtime.settings")
        decision = self._verify_maintenance(evidence)
        self._require_confirmed_maintenance(actor, decision)
        self._require_unconsumed_receipt(decision)
        if "total_mana" in changes:
            raise MagicRuntimeError("total_mana is conserved and cannot be reconfigured")
        unknown = set(changes) - set(asdict(self.limits))
        if unknown:
            raise MagicRuntimeError(f"unknown magic setting: {sorted(unknown)[0]}")
        candidate_data = asdict(self.limits)
        candidate_data.update(changes)
        candidate = MagicLimits(**candidate_data)
        candidate.validate(total_mana=self.total_mana)
        self._validate_limits_against_live_state(candidate)
        return self._append(
            "configure",
            actor=actor,
            locality=None,
            amount=0,
            details={"changes": changes, "act_id": evidence.act_id, "evidence": asdict(evidence), "decision": asdict(decision)},
        )

    def admit_level(self, level: int) -> None:
        if not _is_int(level) or level < 0:
            raise MagicRuntimeError("level must be a non-negative integer")
        if level > self.limits.max_level:
            raise MagicRuntimeError("max_level exceeded")

    def _verify_consequence(self, cast_id: str, commitment: dict[str, Any]) -> ConsequenceDecision:
        if self._consequence_verifier is None:
            raise MagicRuntimeError("consequence verifier unavailable")
        decision = self._consequence_verifier(cast_id, deepcopy(commitment))
        if not isinstance(decision, ConsequenceDecision):
            raise MagicRuntimeError("consequence verifier must return ConsequenceDecision")
        decision.validate()
        return decision

    def _verify_maintenance_act(self, actor: str, evidence: MaintenanceEvidence) -> MaintenanceDecision:
        evidence.validate()
        self._require_unapplied_act(evidence)
        self._require_maintainer(actor, evidence.domain)
        decision = self._verify_maintenance(evidence)
        self._require_confirmed_maintenance(actor, decision)
        self._require_unconsumed_receipt(decision)
        return decision

    def _verify_maintenance(self, evidence: MaintenanceEvidence) -> MaintenanceDecision:
        if self._maintenance_verifier is None:
            raise MagicRuntimeError("maintenance verifier unavailable")
        decision = self._maintenance_verifier(deepcopy(evidence))
        if not isinstance(decision, MaintenanceDecision):
            raise MagicRuntimeError("maintenance verifier must return MaintenanceDecision")
        decision.validate()
        return decision

    def _require_confirmed_maintenance(self, actor: str, decision: MaintenanceDecision) -> None:
        if not decision.confirmed:
            raise MagicRuntimeError("maintenance was not independently confirmed")
        if decision.observer == actor:
            raise MagicRuntimeError("maintenance requires an independent observer")

    def _require_access(self, actor: str, operation: str, locality: str) -> None:
        if self._access_resolver is None or not self._access_resolver(actor, operation, locality):
            raise MagicRuntimeError(f"magic access unavailable: {operation}:{locality}")

    def _require_maintainer(self, actor: str, domain: str) -> None:
        if self._role_resolver is None or not self._role_resolver(actor, self.ROLE_DOMAINS_MAINTAINER, domain):
            raise MagicRuntimeError("Domains Maintainer role unavailable for domain")

    def _require_unapplied_act(self, evidence: MaintenanceEvidence) -> None:
        if evidence.act_id in self._state.maintenance_acts:
            raise MagicRuntimeError("maintenance act already applied")
        if evidence.source_key in self._state.maintenance_sources:
            raise MagicRuntimeError("maintenance source already consumed")

    def _require_unconsumed_receipt(self, decision: MaintenanceDecision) -> None:
        """A verifier response is not reusable authority.

        Checked after confirmation because the receipt is supplied by the
        verifier, not claimed by the source.
        """
        if decision.receipt_id in self._state.maintenance_receipts:
            raise MagicRuntimeError("maintenance receipt already consumed")

    def _consume_maintenance_identity(self, details: dict[str, Any]) -> None:
        """Consume all three replay guards for one maintenance consequence.

        Called from `_apply`, so live operation and ledger replay pass through
        the same boundary. A persisted ledger holding a duplicate is refused on
        open rather than reconstructed into a state that already permitted it.
        """
        act_id = details["act_id"]
        source_key = "{source_kind}:{source_id}".format(**details["evidence"])
        receipt_id = details["decision"]["receipt_id"]
        if act_id in self._state.maintenance_acts:
            raise MagicRuntimeError("maintenance act already applied")
        if source_key in self._state.maintenance_sources:
            raise MagicRuntimeError("maintenance source already consumed")
        if receipt_id in self._state.maintenance_receipts:
            raise MagicRuntimeError("maintenance receipt already consumed")
        self._state.maintenance_acts.add(act_id)
        self._state.maintenance_sources.add(source_key)
        self._state.maintenance_receipts.add(receipt_id)

    def _restoration_allocations(self, locality: str, amount: int) -> list[dict[str, Any]]:
        remaining = amount
        allocations: list[dict[str, Any]] = []
        lots = sorted(
            (lot for lot in self._state.spent.values() if lot.locality == locality),
            key=lambda lot: lot.created_sequence,
        )
        for lot in lots:
            if remaining <= 0:
                break
            restored = min(remaining, lot.amount)
            allocations.append({"cast_id": lot.cast_id, "amount": restored})
            remaining -= restored
        if remaining:
            raise MagicRuntimeError("restoration allocation exceeds eligible spent Mana")
        return allocations

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
        if not _is_int(amount) or amount < 0:
            raise MagicRuntimeError("event amount must be a non-negative integer")
        sequence = len(self._events)
        previous_digest = self._events[-1].digest if self._events else None
        safe_details = deepcopy(details)
        material = {
            "sequence": sequence,
            "operation": operation,
            "actor": actor,
            "locality": locality,
            "amount": amount,
            "details": safe_details,
            "previous_digest": previous_digest,
        }
        digest = self._event_digest(material)
        event = ManaEvent(digest=digest, **material)
        previous_state = deepcopy(self._state)
        previous_events = list(self._events)
        try:
            self._apply(event)
            self._events.append(event)
            self._validate_state()
            if persist:
                self._persist()
        except Exception:
            self._state = previous_state
            self._events = previous_events
            raise
        # Return a detached record so callers cannot mutate ledger internals.
        return deepcopy(event)

    def _apply(self, event: ManaEvent) -> None:
        operation = event.operation
        locality = event.locality
        actor = event.actor
        amount = event.amount
        if operation == "genesis":
            total_mana = event.details["total_mana"]
            limits = MagicLimits(**event.details["limits"])
            limits.validate(total_mana=total_mana)
            self._state = _State(total_mana=total_mana, limits=limits, ambient={str(locality): amount})
        elif operation == "flow":
            target = event.details["target"]
            self._move_ambient(locality, -amount)
            self._move_ambient(target, amount)
        elif operation == "claim":
            self._move_ambient(locality, -amount)
            self._move_claim(locality, actor, amount)
        elif operation in {"release", "drain"}:
            self._move_claim(locality, actor, -amount)
            self._move_ambient(locality, amount)
        elif operation == "commit":
            cast_id = event.details["cast_id"]
            if cast_id in self._state.cast_ids:
                raise MagicRuntimeError(f"cast id already used for Mana: {cast_id}")
            self._move_claim(locality, actor, -amount)
            self._state.committed[cast_id] = {"actor": actor, "locality": locality, "amount": amount}
            self._state.cast_ids.add(cast_id)
        elif operation == "settle":
            cast_id = event.details["cast_id"]
            commitment = self._state.committed.pop(cast_id)
            spent = event.details["spent"]
            released = event.details["released"]
            if commitment["amount"] != spent + released:
                raise MagicRuntimeError("invalid settlement")
            if spent:
                self._state.spent[cast_id] = SpentLot(
                    cast_id=cast_id,
                    actor=str(actor),
                    locality=str(locality),
                    amount=spent,
                    created_sequence=event.sequence,
                )
            if released:
                self._move_claim(locality, actor, released)
        elif operation == "maintenance":
            allocations = event.details["restored_from"]
            if sum(item["amount"] for item in allocations) != amount:
                raise MagicRuntimeError("restoration allocations do not match event amount")
            for item in allocations:
                cast_id = item["cast_id"]
                restored = item["amount"]
                lot = self._state.spent.get(cast_id)
                if lot is None or lot.locality != str(locality) or lot.amount < restored:
                    raise MagicRuntimeError("restoration references ineligible spent Mana")
                remaining = lot.amount - restored
                if remaining:
                    self._state.spent[cast_id] = SpentLot(
                        cast_id=lot.cast_id,
                        actor=lot.actor,
                        locality=lot.locality,
                        amount=remaining,
                        created_sequence=lot.created_sequence,
                    )
                else:
                    del self._state.spent[cast_id]
            if amount:
                self._move_ambient(locality, amount)
            self._consume_maintenance_identity(event.details)
        elif operation == "configure":
            data = asdict(self._state.limits)
            data.update(event.details["changes"])
            candidate = MagicLimits(**data)
            candidate.validate(total_mana=self.total_mana)
            self._state.limits = candidate
            self._consume_maintenance_identity(event.details)
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
        if self._accounted_total() != self.total_mana:
            raise MagicRuntimeError("Mana conservation violated")
        if self._network_active() > self.limits.max_network:
            raise MagicRuntimeError("live state exceeds max_network")
        if self._committed_total() > self.limits.max_committed:
            raise MagicRuntimeError("live state exceeds max_committed")
        localities = set(self._state.ambient) | {place for place, _ in self._state.claimed}
        localities |= {item["locality"] for item in self._state.committed.values()}
        for locality in localities:
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
            + self.spent_total()
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
            if not isinstance(raw, dict):
                raise MagicRuntimeError("magic ledger event must be a mapping")
            sequence = raw.get("sequence")
            amount = raw.get("amount")
            if not _is_int(sequence) or sequence < 0:
                raise MagicRuntimeError("magic ledger sequence is invalid")
            if not _is_int(amount) or amount < 0:
                raise MagicRuntimeError("magic ledger amount is invalid")
            expected_previous = self._events[-1].digest if self._events else None
            details = raw.get("details") or {}
            if not isinstance(details, dict):
                raise MagicRuntimeError("magic ledger event details must be a mapping")
            material = {
                "sequence": sequence,
                "operation": raw["operation"],
                "actor": raw.get("actor"),
                "locality": raw.get("locality"),
                "amount": amount,
                "details": deepcopy(details),
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
        if not _is_int(value) or value <= 0:
            raise MagicRuntimeError("amount must be a positive integer")

    @staticmethod
    def _name(value: Any, name: str) -> None:
        if not isinstance(value, str) or not value:
            raise MagicRuntimeError(f"{name} must be a non-empty string")

    @staticmethod
    def _prune(mapping: dict[Any, int], key: Any) -> None:
        if mapping.get(key) == 0:
            mapping.pop(key, None)
