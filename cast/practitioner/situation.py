"""Situated matching of Cast Requirements to concrete capability receipts.

A Requirement compiles into a typed **demand**: what kind of mechanism must be
available, which identity constraints must hold, and what capacity relation
must be satisfied. A demand binds to the exact `CapabilityReceipt` that proves
it, not to the first receipt that happens to expose the same operation verb.

Capacity is not one universal scalar comparison. A numeric ceiling, a
permission set, a Scope region, an Authority attenuation, a protocol operation
set, and a control boundary are six different relations, and collapsing them
into `>=` was the defect. Each relation is a small named function, so a new
kind is added without importing provider-specific types.

Format declares demand and protocol semantics. Situation and CastPlan own the
situated matching. Concrete receipt identity does not move back into portable
`SPELL.md`.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Callable, Mapping


class CapabilityMatchError(ValueError):
    """A demand could not be expressed, as distinct from not being satisfied."""


@dataclass(frozen=True)
class CapabilityReceipt:
    """One concrete Environment mechanism available in this Situation."""

    name: str
    environment: str
    operations: tuple[str, ...]
    status: str
    authority: str
    locator: str
    evidence: str
    protocol: str | None = None
    subject: str | None = None
    #: Kind-specific capacity properties. Read only by the relation named in a
    #: demand, so an unrecognised key here is inert rather than misinterpreted.
    capacity: Mapping[str, Any] = field(default_factory=dict)

    def supports(self, operation: str) -> bool:
        return self.status == "available" and operation in self.operations


@dataclass(frozen=True)
class Demand:
    """What a Requirement needs, in terms a matcher can check.

    Identity constraints left as None are unconstrained. Supplying more of them
    is how an otherwise ambiguous match is resolved exactly.
    """

    operation: str
    relation: str = "operation"
    capability: str | None = None
    protocol: str | None = None
    environment: str | None = None
    authority: str | None = None
    subject: str | None = None
    locator: str | None = None
    capacity: Mapping[str, Any] = field(default_factory=dict)
    #: True when the capability must be narrowed before Technique execution.
    attenuate: bool = False


@dataclass(frozen=True)
class RequirementMatch:
    """Why exactly this receipt was selected for exactly this Requirement."""

    requirement_id: str
    demand: Demand
    receipt: CapabilityReceipt
    relation: str
    detail: Mapping[str, Any]
    #: The capability to execute through. Equal to `receipt` unless the demand
    #: required narrowing, in which case it is the attenuated handle.
    handle: CapabilityReceipt

    @property
    def attenuated(self) -> bool:
        return self.handle != self.receipt


# -- capacity relations ---------------------------------------------------
#
# Each returns (satisfied, detail). Detail is retained as match evidence, so a
# CAST record can point at the numbers or sets that made the decision.


def _relation_operation(demand: Demand, receipt: CapabilityReceipt) -> tuple[bool, dict[str, Any]]:
    """No capacity claim beyond exposing the operation. The simple case."""
    return True, {}


def _relation_quota(demand: Demand, receipt: CapabilityReceipt) -> tuple[bool, dict[str, Any]]:
    """available >= demanded"""
    demanded = demand.capacity.get("demanded")
    available = receipt.capacity.get("available")
    if not isinstance(demanded, int) or isinstance(demanded, bool):
        raise CapabilityMatchError("quota demand requires an integer 'demanded'")
    if not isinstance(available, int) or isinstance(available, bool):
        return False, {"reason": "receipt declares no integer quota", "demanded": demanded}
    return available >= demanded, {"demanded": demanded, "available": available}


def _relation_permissions(demand: Demand, receipt: CapabilityReceipt) -> tuple[bool, dict[str, Any]]:
    """granted superset-of required"""
    required = frozenset(demand.capacity.get("required", ()))
    granted = frozenset(receipt.capacity.get("granted", ()))
    missing = required - granted
    return not missing, {
        "required": sorted(required),
        "granted": sorted(granted),
        "missing": sorted(missing),
    }


def _relation_scope(demand: Demand, receipt: CapabilityReceipt) -> tuple[bool, dict[str, Any]]:
    """granted region subset-of resolved admissible region

    The containment runs the opposite way from permissions. A capability that
    can reach further than the admissible region is not narrower for being
    larger, which is exactly the confusion a single scalar comparison invites.
    """
    admissible = frozenset(demand.capacity.get("admissible", ()))
    region = frozenset(receipt.capacity.get("region", ()))
    outside = region - admissible
    return not outside, {
        "admissible": sorted(admissible),
        "region": sorted(region),
        "outside": sorted(outside),
    }


def _relation_authority(demand: Demand, receipt: CapabilityReceipt) -> tuple[bool, dict[str, Any]]:
    """injected authority subset-of resolved authority"""
    resolved = frozenset(demand.capacity.get("resolved", ()))
    grants = frozenset(receipt.capacity.get("grants", ()))
    excess = grants - resolved
    return not excess, {
        "resolved": sorted(resolved),
        "grants": sorted(grants),
        "excess": sorted(excess),
    }


def _relation_protocol(demand: Demand, receipt: CapabilityReceipt) -> tuple[bool, dict[str, Any]]:
    """provided operations superset-of required operations"""
    required = frozenset(demand.capacity.get("required_operations", ()))
    provided = frozenset(receipt.capacity.get("operations", ()))
    missing = required - provided
    return not missing, {
        "required_operations": sorted(required),
        "provided_operations": sorted(provided),
        "missing": sorted(missing),
    }


def _relation_control(demand: Demand, receipt: CapabilityReceipt) -> tuple[bool, dict[str, Any]]:
    """mechanism can contain or interrupt the required execution boundary"""
    boundary = demand.capacity.get("boundary")
    contains = frozenset(receipt.capacity.get("contains", ()))
    if not isinstance(boundary, str) or not boundary:
        raise CapabilityMatchError("control demand requires a named 'boundary'")
    return boundary in contains, {"boundary": boundary, "contains": sorted(contains)}


RelationFn = Callable[[Demand, CapabilityReceipt], "tuple[bool, dict[str, Any]]"]

RELATIONS: dict[str, RelationFn] = {
    "operation": _relation_operation,
    "quota": _relation_quota,
    "permissions": _relation_permissions,
    "scope": _relation_scope,
    "authority": _relation_authority,
    "protocol": _relation_protocol,
    "control": _relation_control,
}


# -- attenuation ----------------------------------------------------------
#
# Narrowing a capability before execution is relation-specific. A relation with
# no attenuator cannot honour `attenuate=True`, and compilation says so rather
# than handing the broader capability through.


def _attenuate_quota(demand: Demand, receipt: CapabilityReceipt) -> CapabilityReceipt:
    capacity = dict(receipt.capacity)
    capacity["available"] = demand.capacity["demanded"]
    return replace(receipt, capacity=capacity, name=f"{receipt.name} (attenuated)")


def _attenuate_permissions(demand: Demand, receipt: CapabilityReceipt) -> CapabilityReceipt:
    capacity = dict(receipt.capacity)
    granted = frozenset(receipt.capacity.get("granted", ()))
    capacity["granted"] = tuple(sorted(granted & frozenset(demand.capacity.get("required", ()))))
    return replace(receipt, capacity=capacity, name=f"{receipt.name} (attenuated)")


def _attenuate_scope(demand: Demand, receipt: CapabilityReceipt) -> CapabilityReceipt:
    capacity = dict(receipt.capacity)
    region = frozenset(receipt.capacity.get("region", ()))
    capacity["region"] = tuple(sorted(region & frozenset(demand.capacity.get("admissible", ()))))
    return replace(receipt, capacity=capacity, name=f"{receipt.name} (attenuated)")


def _attenuate_authority(demand: Demand, receipt: CapabilityReceipt) -> CapabilityReceipt:
    capacity = dict(receipt.capacity)
    grants = frozenset(receipt.capacity.get("grants", ()))
    capacity["grants"] = tuple(sorted(grants & frozenset(demand.capacity.get("resolved", ()))))
    return replace(receipt, capacity=capacity, name=f"{receipt.name} (attenuated)")


ATTENUATORS: dict[str, Callable[[Demand, CapabilityReceipt], CapabilityReceipt]] = {
    "quota": _attenuate_quota,
    "permissions": _attenuate_permissions,
    "scope": _attenuate_scope,
    "authority": _attenuate_authority,
}


@dataclass
class Situation:
    """Runtime view of the current cast, not portable Spell state."""

    id: str
    session_id: str
    caster: dict[str, Any]
    target: Any
    environments: tuple[str, ...] = ()
    capabilities: tuple[CapabilityReceipt, ...] = ()
    present_familiars: tuple[str, ...] = ()
    observations: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CastPlan:
    matches: dict[str, RequirementMatch]
    gaps: tuple[str, ...]

    @property
    def ready(self) -> bool:
        return not self.gaps

    @property
    def requirements(self) -> dict[str, CapabilityReceipt]:
        """The exact receipt selected per Requirement."""
        return {key: match.receipt for key, match in self.matches.items()}

    def handle(self, requirement_id: str) -> CapabilityReceipt:
        """The capability execution may use for this Requirement.

        The attenuated handle where narrowing was required, otherwise the
        receipt itself. A Technique is given this, never the broader receipt.
        """
        return self.matches[requirement_id].handle


_IDENTITY_CONSTRAINTS = (
    ("capability", "name"),
    ("protocol", "protocol"),
    ("environment", "environment"),
    ("authority", "authority"),
    ("subject", "subject"),
    ("locator", "locator"),
)


def as_demand(value: str | Demand) -> Demand:
    """Accept a bare operation verb so simple one-receipt cases stay simple."""
    if isinstance(value, Demand):
        return value
    if isinstance(value, str) and value:
        return Demand(operation=value)
    raise CapabilityMatchError("a Requirement demand must be a Demand or a non-empty operation name")


def _identity_mismatch(demand: Demand, receipt: CapabilityReceipt) -> str | None:
    for demand_field, receipt_field in _IDENTITY_CONSTRAINTS:
        wanted = getattr(demand, demand_field)
        if wanted is not None and getattr(receipt, receipt_field) != wanted:
            return demand_field
    return None


def compile_cast_plan(
    requirements: Mapping[str, str | Demand],
    situation: Situation,
) -> CastPlan:
    """Bind each Requirement to the one receipt that proves its typed demand.

    Fails closed in three ways rather than guessing: no admissible receipt, more
    than one admissible receipt, or a required narrowing the relation cannot
    perform.

    This knows nothing about providers. OWL_ENGINE-compatible receipts can be
    projected into CapabilityReceipt and supplied here.
    """

    matches: dict[str, RequirementMatch] = {}
    gaps: list[str] = []

    for requirement_id, raw in requirements.items():
        demand = as_demand(raw)
        relation = RELATIONS.get(demand.relation)
        if relation is None:
            raise CapabilityMatchError(f"unknown capacity relation: {demand.relation}")

        admissible: list[tuple[CapabilityReceipt, dict[str, Any]]] = []
        for receipt in situation.capabilities:
            if not receipt.supports(demand.operation):
                continue
            if _identity_mismatch(demand, receipt) is not None:
                continue
            satisfied, detail = relation(demand, receipt)
            if satisfied:
                admissible.append((receipt, detail))

        if not admissible:
            gaps.append(f"capability-missing:{requirement_id}:{demand.operation}")
            continue

        if len(admissible) > 1:
            names = ",".join(sorted(receipt.name for receipt, _ in admissible))
            gaps.append(f"capability-ambiguous:{requirement_id}:{demand.operation}:{names}")
            continue

        receipt, detail = admissible[0]
        handle = receipt
        if demand.attenuate:
            attenuator = ATTENUATORS.get(demand.relation)
            if attenuator is None:
                gaps.append(f"attenuation-unavailable:{requirement_id}:{demand.relation}")
                continue
            handle = attenuator(demand, receipt)

        matches[requirement_id] = RequirementMatch(
            requirement_id=requirement_id,
            demand=demand,
            receipt=receipt,
            relation=demand.relation,
            detail=detail,
            handle=handle,
        )

    return CastPlan(matches=matches, gaps=tuple(gaps))
