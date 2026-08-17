"""The closed-plan contract for the 0.7 crossing: CrossingPlan, Brink, Closure.

0.7 couples three independent algebras -- Mana, Capacity, and Obligations --
through one ordered Cast crossing. Coupling them is not merging them. A
CrossingPlan holds each in its own shape and relates them explicitly:

    Capacity      cast.practitioner.situation.CastPlan
                  typed demands bound to exact receipts, with attenuated handles

    Obligations   cast.practitioner.obligations.ObligationPlan
                  compiled properties bound to discharge mechanisms of their kind

    Mana          ManaParticipation, declarative only
                  what this Cast plans to claim and commit, never performed here

`ObligationPlan` already carries its `capability_plan`, so this composes rather
than re-implements. Nothing here flattens an obligation into a capability demand
or a Mana cost into either: #47 refused that structurally and this preserves it.

**This module plans and seals. It does not execute.** No Mana moves here -- #16
owns integrating the conserved runtime with the Cast lifecycle. No obligation is
discharged here -- #32 owns that and #35 owns the observation seam that decides
status. What this owns is the moment between: the last point at which nothing
has happened, and the act that makes what is about to happen unforgeable.

Three terms, and the whole contract is in keeping them apart.

**Brink** is a state of the world, not of the plan: zero Cast-attributable
effect and zero Cast-attributable Mana commitment. It says nothing about other
Casts, existing claims, or unrelated Environment activity. It is observed, never
asserted -- the Kernel specifies the contract and the Environment owns the
mechanism, exactly as it does for Scope, Authority, consequence, and blast
radius.

**Closure** is the act that makes the authorized plan identity immutable. After
it, `plan_digest` names exactly one configuration, one set of bindings, and one
set of obligations, and no later evidence can quietly become a different plan.

**What may still move.** Findings, statuses, outcome, residuals and settlement
all evolve after Closure, and none of them is part of the closed plan. That
separation is the point: a record that could not change would be useless, and a
plan that could change would be unforgeable in name only.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass, field
from hashlib import sha256
import json
from typing import Any

from practitioner.obligations import ObligationPlan
from practitioner.situation import CapabilityReceipt, CastPlan, Demand

#: The plan-identity generation this module seals. Changing what
#: `canonical_material` includes changes what a digest means, so it is named
#: rather than implied.
CROSSING_PLAN_VERSION = "0.7-draft"


class CrossingPlanError(ValueError):
    """A crossing plan is malformed, unready, or was closed illegally."""


# -- Mana participation ---------------------------------------------------


@dataclass(frozen=True)
class ManaParticipation:
    """What this Cast plans to claim and commit, in one locality.

    Declarative. Nothing here moves Mana, and this type deliberately cannot:
    it holds intent so that Closure can seal it, and #16 owns the runtime that
    acts on it.

    `commit` may not exceed `claim`. A plan that intends to commit more than it
    claimed is not a tight budget, it is an unfunded one, and it fails at
    construction rather than at the moment the commitment is attempted.
    """

    locality: str
    participant: str
    claim: int
    commit: int

    def __post_init__(self) -> None:
        for name in ("locality", "participant"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise CrossingPlanError(f"Mana participation requires {name}")
        for name in ("claim", "commit"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise CrossingPlanError(f"Mana {name} must be a non-negative integer")
        if self.commit > self.claim:
            raise CrossingPlanError(
                f"planned commit {self.commit} exceeds planned claim {self.claim} "
                f"in {self.locality}"
            )

    def as_material(self) -> dict[str, Any]:
        return {
            "locality": self.locality,
            "participant": self.participant,
            "claim": self.claim,
            "commit": self.commit,
        }


# -- evidence contracts ---------------------------------------------------


@dataclass(frozen=True)
class EvidenceContract:
    """What evidence would discharge one obligation, and who may produce it.

    Sealed into the plan so that the standard cannot be chosen after the fact to
    fit whatever evidence happened to appear. #35 owns evaluating against these;
    this owns fixing them before anything runs.
    """

    obligation_id: str
    contract: str
    observer: str

    def __post_init__(self) -> None:
        for name in ("obligation_id", "contract", "observer"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise CrossingPlanError(f"an evidence contract requires {name}")

    def as_material(self) -> dict[str, Any]:
        return {
            "obligation_id": self.obligation_id,
            "contract": self.contract,
            "observer": self.observer,
        }


# -- residual bounds ------------------------------------------------------


@dataclass(frozen=True)
class ResidualBounds:
    """Which residual kinds this crossing may produce without that being a breach.

    A residual outside the bound is not noise to be filtered later. It is the
    crossing exceeding what it was authorized to leave behind, and sealing the
    bound is what makes that judgement possible after the fact rather than a
    matter of whoever reads the record.

    Empty means no residual is tolerated, which is a strong claim and is
    therefore never the default -- it must be written.
    """

    permitted: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.permitted, tuple):
            raise CrossingPlanError("residual bounds must be a tuple of kinds")
        for kind in self.permitted:
            if not isinstance(kind, str) or not kind:
                raise CrossingPlanError("a residual kind must be a non-empty string")

    def exceeded_by(self, kinds: Sequence[str]) -> tuple[str, ...]:
        return tuple(kind for kind in kinds if kind not in self.permitted)

    def as_material(self) -> dict[str, Any]:
        return {"permitted": sorted(self.permitted)}


# -- the Brink ------------------------------------------------------------


@dataclass(frozen=True)
class BrinkFinding:
    """Observed state immediately before Closure.

    `effect_delta` and `mana_delta` are Cast-attributable only. Other Casts,
    pre-existing claims and unrelated Environment activity are not this Cast's
    doing and are not prohibited by being non-zero -- reading them as violations
    would make the Brink unreachable on any busy runtime.
    """

    effect_delta: int
    mana_delta: int
    observations: tuple[Mapping[str, Any], ...] = ()
    unobservable: tuple[str, ...] = ()

    @property
    def at_brink(self) -> bool:
        return self.effect_delta == 0 and self.mana_delta == 0 and not self.unobservable

    def reasons(self) -> tuple[str, ...]:
        out: list[str] = []
        if self.effect_delta != 0:
            out.append(f"brink-effect-already-applied: {self.effect_delta}")
        if self.mana_delta != 0:
            out.append(f"brink-mana-already-committed: {self.mana_delta}")
        for name in self.unobservable:
            out.append(f"brink-unobservable: {name}")
        return tuple(out)

    def as_material(self) -> dict[str, Any]:
        return {
            "effect_delta": self.effect_delta,
            "mana_delta": self.mana_delta,
            "unobservable": sorted(self.unobservable),
        }


def observe_brink(
    effect_probe: Callable[[], int] | None,
    mana_probe: Callable[[], int] | None,
) -> BrinkFinding:
    """Ask the Environment whether this Cast has already done anything.

    A missing probe is recorded as `unobservable`, not assumed to be zero. An
    unobserved Brink that closes anyway would let a Cast claim it started from
    nothing on the strength of nobody having looked -- which is the same defect
    as a Technique certifying its own containment, one phase earlier.

    A raising probe is also unobservable. A probe that fails has not told us the
    delta is zero; it has told us nothing.
    """
    unobservable: list[str] = []
    observations: list[Mapping[str, Any]] = []

    def read(name: str, probe: Callable[[], int] | None) -> int:
        if probe is None:
            unobservable.append(name)
            return 0
        try:
            value = probe()
        except Exception as exc:  # noqa: BLE001 -- any failure means "unknown"
            unobservable.append(f"{name}: {type(exc).__name__}: {exc}")
            return 0
        if not isinstance(value, int) or isinstance(value, bool):
            unobservable.append(f"{name}: probe returned {type(value).__name__}, not int")
            return 0
        observations.append({"probe": name, "value": value})
        return value

    effect_delta = read("effect", effect_probe)
    mana_delta = read("mana", mana_probe)
    return BrinkFinding(
        effect_delta=effect_delta,
        mana_delta=mana_delta,
        observations=tuple(observations),
        unobservable=tuple(unobservable),
    )


# -- the plan -------------------------------------------------------------


def _receipt_material(receipt: CapabilityReceipt) -> dict[str, Any]:
    """Identity and capacity of one receipt, as sealed.

    Capacity is included because an attenuated handle differs from its receipt
    only there. Omitting it would let a Scope or Authority narrowing be swapped
    after Closure without changing the digest, which is precisely the swap this
    contract exists to catch.
    """
    return {
        "name": receipt.name,
        "environment": receipt.environment,
        "operations": sorted(receipt.operations),
        "status": receipt.status,
        "authority": receipt.authority,
        "locator": receipt.locator,
        "evidence": receipt.evidence,
        "protocol": receipt.protocol,
        "subject": receipt.subject,
        "capacity": _plain(receipt.capacity),
    }


def _demand_material(demand: Demand | None) -> dict[str, Any] | None:
    if demand is None:
        return None
    return {
        "operation": demand.operation,
        "relation": demand.relation,
        "capability": demand.capability,
        "protocol": demand.protocol,
        "environment": demand.environment,
        "authority": demand.authority,
        "subject": demand.subject,
        "locator": demand.locator,
        "capacity": _plain(demand.capacity),
        "attenuate": demand.attenuate,
    }


def _plain(value: Any) -> Any:
    """Reduce mappings and sequences to plain, order-stable JSON material."""
    if isinstance(value, Mapping):
        return {str(k): _plain(value[k]) for k in sorted(value, key=str)}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _capacity_material(plan: CastPlan) -> dict[str, Any]:
    return {
        requirement_id: {
            "demand": _demand_material(match.demand),
            "relation": match.relation,
            "receipt": _receipt_material(match.receipt),
            "handle": _receipt_material(match.handle),
            "attenuated": match.attenuated,
        }
        for requirement_id, match in sorted(plan.matches.items())
    }


def _obligations_material(plan: ObligationPlan) -> dict[str, Any]:
    material: dict[str, Any] = {}
    for obligation_id, binding in sorted(plan.bindings.items()):
        obligation = binding.obligation
        material[obligation_id] = {
            "requirement_id": obligation.requirement_id,
            "kind": obligation.kind,
            "phase": obligation.phase,
            "required": obligation.required,
            "demand": _demand_material(obligation.demand),
            "spec": _plain(obligation.spec),
            "mechanism": None
            if binding.mechanism is None
            else {
                "id": binding.mechanism.id,
                "kind": binding.mechanism.kind,
                "provenance": binding.mechanism.provenance,
                "evidence_contract": binding.mechanism.evidence_contract,
            },
            "capability_requirement_id": binding.capability_requirement_id,
        }
    return material


@dataclass(frozen=True)
class CrossingPlan:
    """The complete situated plan immediately before Closure.

    Holds the three algebras in their own shapes and relates them. It does not
    merge them, and every accessor here reads one of them rather than a blend.
    """

    configuration: Mapping[str, Any]
    obligations: ObligationPlan
    mana: tuple[ManaParticipation, ...] = ()
    evidence_contracts: tuple[EvidenceContract, ...] = ()
    residual_bounds: ResidualBounds = field(default_factory=lambda: ResidualBounds(()))

    def __post_init__(self) -> None:
        if not isinstance(self.configuration, Mapping) or not self.configuration:
            raise CrossingPlanError("a crossing plan requires a resolved configuration")
        seen: set[str] = set()
        for contract in self.evidence_contracts:
            if contract.obligation_id in seen:
                raise CrossingPlanError(
                    f"two evidence contracts for {contract.obligation_id}; "
                    "one obligation has one standard"
                )
            seen.add(contract.obligation_id)

    @property
    def capacity(self) -> CastPlan:
        """The capability plan. Obligations already carry it; this names it."""
        return self.obligations.capability_plan

    @property
    def gaps(self) -> tuple[str, ...]:
        """Everything unbound, from either algebra, without merging them."""
        return tuple(self.obligations.gaps) + tuple(self.capacity.gaps)

    @property
    def ready(self) -> bool:
        return not self.gaps

    def evidence_contract_for(self, obligation_id: str) -> EvidenceContract | None:
        for contract in self.evidence_contracts:
            if contract.obligation_id == obligation_id:
                return contract
        return None


def canonical_material(plan: CrossingPlan) -> dict[str, Any]:
    """Exactly what `plan_digest` is taken over.

    Separated from the digest so a reader can see what is sealed without
    reading a hash, and so a change to what is sealed is a visible change to
    this function rather than an invisible change to a hex string.
    """
    return {
        "crossing_plan_version": CROSSING_PLAN_VERSION,
        "configuration": _plain(plan.configuration),
        "capacity": _capacity_material(plan.capacity),
        "obligations": _obligations_material(plan.obligations),
        "mana": [participation.as_material() for participation in plan.mana],
        "evidence_contracts": [
            contract.as_material()
            for contract in sorted(plan.evidence_contracts, key=lambda c: c.obligation_id)
        ],
        "residual_bounds": plan.residual_bounds.as_material(),
    }


def plan_digest(plan: CrossingPlan) -> str:
    """Exact plan identity.

    Canonically equivalent plans yield the same digest; any material change
    yields a different one. This is integrity, not truth and not provenance --
    it says the plan is the one that was closed, never that closing it was wise.
    """
    encoded = json.dumps(
        canonical_material(plan), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return "sha256:" + sha256(encoded).hexdigest()


# -- Closure --------------------------------------------------------------


@dataclass(frozen=True)
class ClosedPlan:
    """An authorized plan whose identity is now immutable.

    Carries no findings, no statuses, no outcome and no settlement. Those evolve
    and this does not, which is the separation Closure exists to create.
    """

    plan: CrossingPlan
    digest: str
    brink: BrinkFinding

    def material(self) -> dict[str, Any]:
        return canonical_material(self.plan)


def close(plan: CrossingPlan, brink: BrinkFinding) -> ClosedPlan:
    """Seal the plan, or refuse.

    Refuses when the plan has gaps, and when the Brink is not clean. Both are
    fail-closed for the same reason: a Cast that closes over an unbound
    obligation, or over a world where it has already acted, has sealed a
    description of something other than what will happen.

    Closure snapshots the complete plan graph. `@dataclass(frozen=True)` only
    freezes attribute assignment on the outer objects; nested mappings and
    capacity/spec structures may still be mutable. Retaining the caller's plan
    object would therefore let post-Closure mutation rewrite the supposedly
    immutable closed material and make `verify()` compare the changed object to
    itself. The deep snapshot is the actual immutability boundary.
    """
    reasons: list[str] = []
    if not plan.ready:
        reasons.extend(f"closure-gap: {gap}" for gap in plan.gaps)
    if not brink.at_brink:
        reasons.extend(brink.reasons())
    if reasons:
        raise CrossingPlanError("; ".join(reasons))
    frozen_plan = deepcopy(plan)
    return ClosedPlan(plan=frozen_plan, digest=plan_digest(frozen_plan), brink=deepcopy(brink))


# -- post-Closure verification -------------------------------------------


@dataclass(frozen=True)
class PlanViolation:
    """One way an observed plan differs from the plan that was closed."""

    path: str
    closed: Any
    observed: Any

    def describe(self) -> str:
        return f"closed-plan-violation at {self.path}: closed={self.closed!r} observed={self.observed!r}"


def _diff(closed: Any, observed: Any, path: str) -> list[PlanViolation]:
    if isinstance(closed, dict) and isinstance(observed, dict):
        out: list[PlanViolation] = []
        for key in sorted(set(closed) | set(observed)):
            here = f"{path}.{key}" if path else str(key)
            if key not in closed:
                out.append(PlanViolation(here, None, observed[key]))
            elif key not in observed:
                out.append(PlanViolation(here, closed[key], None))
            else:
                out.extend(_diff(closed[key], observed[key], here))
        return out
    if isinstance(closed, list) and isinstance(observed, list):
        out = []
        for index in range(max(len(closed), len(observed))):
            here = f"{path}[{index}]"
            if index >= len(closed):
                out.append(PlanViolation(here, None, observed[index]))
            elif index >= len(observed):
                out.append(PlanViolation(here, closed[index], None))
            else:
                out.extend(_diff(closed[index], observed[index], here))
        return out
    if closed != observed:
        return [PlanViolation(path or "(root)", closed, observed)]
    return []


def verify(closed: ClosedPlan, observed: CrossingPlan) -> tuple[PlanViolation, ...]:
    """Compare what is about to execute against what was closed.

    Returns every difference rather than the first, and names each by path, so
    a swapped target and a swapped binding are distinguishable in the record
    instead of collapsing into one 'plan changed'.

    A caller that only needs the yes-or-no can read the digest; this exists for
    the case where the answer is no and someone has to say what moved.
    """
    return tuple(_diff(closed.material(), canonical_material(observed), ""))


def digest_matches(closed: ClosedPlan, observed: CrossingPlan) -> bool:
    """The cheap check. `verify` says what moved; this says whether anything did."""
    return closed.digest == plan_digest(observed)
