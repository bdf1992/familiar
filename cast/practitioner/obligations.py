"""Requirements compile into typed Runtime Obligations.

A concrete capability proves that a mechanism exists and has sufficient typed
capacity. It cannot by itself prove every property of the resulting execution
or world state. Collapsing every Requirement into `Requirement -> Capability`
would recreate the operation-name-lookup error one layer up: the shape would be
typed, and it would still be the wrong shape for a property that is not about a
mechanism at all.

So a Requirement compiles into one or more obligations, each naming what kind
of evidence or control is required, and each discharged by a situated
mechanism, observer, monitor, verifier, or proof checker.

Six classes, and they are not variations of one thing:

```text
capability gate    an effect path needs a capability with sufficient capacity
state predicate    a before/after condition over resolved state
temporal monitor   a property over an ordered trace, not one instant
global invariant   a law over whole-runtime state, owned by no Technique
semantic trial     behavioural evidence that the intended Effect was realized
provenance proof   evidence carrying attributable observer or signer identity
```

One Requirement may compile to several. Scope needs a capability gate for the
attenuated effect path *and* post-observation of downstream residuals. Mana
conservation needs no per-Technique capability at all.

Formal methods are optional mechanisms, not protocol law. A prover, a model
checker, a temporal monitor, a policy engine, a property suite, or an
adversarial evaluator may each discharge an obligation when the Environment
accepts its evidence contract. **Checker output is evidence, never authority**,
so every outcome retains the provenance of whatever produced it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Mapping, Sequence

from .situation import CastPlan, Demand, Situation, compile_cast_plan

CAPABILITY_GATE = "capability_gate"
STATE_PREDICATE = "state_predicate"
TEMPORAL_MONITOR = "temporal_monitor"
GLOBAL_INVARIANT = "global_invariant"
SEMANTIC_TRIAL = "semantic_trial"
PROVENANCE_PROOF = "provenance_proof"

OBLIGATION_KINDS = (
    CAPABILITY_GATE,
    STATE_PREDICATE,
    TEMPORAL_MONITOR,
    GLOBAL_INVARIANT,
    SEMANTIC_TRIAL,
    PROVENANCE_PROOF,
)

PHASES = ("before", "during", "after")

#: An obligation in one of these phases must have a discharge path before
#: closure. An after-phase obligation may be evaluated once consequence exists.
PRE_CLOSURE_PHASES = ("before", "during")

DISCHARGED = "discharged"
VIOLATED = "violated"
UNRESOLVED = "unresolved"
NOT_APPLICABLE = "not_applicable"


class ObligationError(ValueError):
    """An obligation or mechanism could not be expressed."""


@dataclass(frozen=True)
class RuntimeObligation:
    """What a Requirement demands of the runtime, in one evidence class.

    Separate from portable Spell semantics: a Spell declares the Requirement,
    and this is the situated compilation of it. Separate from a capability
    receipt: only `capability_gate` carries a demand at all.
    """

    id: str
    requirement_id: str
    kind: str
    phase: str
    required: bool = True
    #: capability_gate only. The typed demand handed to the #13 matcher.
    demand: Demand | None = None
    spec: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.kind not in OBLIGATION_KINDS:
            raise ObligationError(f"unknown obligation kind: {self.kind}")
        if self.phase not in PHASES:
            raise ObligationError(f"unknown obligation phase: {self.phase}")
        if self.kind == CAPABILITY_GATE and self.demand is None:
            raise ObligationError(f"{self.id}: a capability gate requires a demand")
        if self.kind != CAPABILITY_GATE and self.demand is not None:
            raise ObligationError(
                f"{self.id}: only a capability gate carries a demand; "
                f"{self.kind} is not a capability lookup"
            )


@dataclass(frozen=True)
class DischargeMechanism:
    """A situated mechanism that may discharge obligations of one kind.

    `provenance` names what produced the evidence. It is retained on every
    outcome because a checker's verdict is evidence about a property, never
    authority over whether the property matters.
    """

    id: str
    kind: str
    provenance: str
    evidence_contract: str
    check: Callable[[RuntimeObligation, Mapping[str, Any]], Any]

    def __post_init__(self) -> None:
        if self.kind not in OBLIGATION_KINDS:
            raise ObligationError(f"unknown mechanism kind: {self.kind}")
        if self.kind == CAPABILITY_GATE:
            raise ObligationError(
                "capability gates are discharged by the capability matcher, "
                "not by a registered checker"
            )
        for name in ("id", "provenance", "evidence_contract"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                raise ObligationError(f"discharge mechanism requires {name}")


@dataclass(frozen=True)
class ObligationBinding:
    obligation: RuntimeObligation
    mechanism: DischargeMechanism | None = None
    #: capability_gate only: the requirement id under which the matcher bound it.
    capability_requirement_id: str | None = None


@dataclass(frozen=True)
class ObligationOutcome:
    obligation_id: str
    requirement_id: str
    kind: str
    phase: str
    status: str
    mechanism_id: str | None
    provenance: str | None
    detail: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ObligationPlan:
    """The compiled obligations, their discharge paths, and what has none."""

    bindings: dict[str, ObligationBinding]
    gaps: tuple[str, ...]
    capability_plan: CastPlan

    @property
    def ready(self) -> bool:
        return not self.gaps

    def mechanism_for(self, obligation_id: str) -> DischargeMechanism | None:
        return self.bindings[obligation_id].mechanism


def _self_certifying(obligation: RuntimeObligation, mechanism: DischargeMechanism) -> bool:
    """A candidate cannot supply the evidence that promotes itself.

    Narrow on purpose: #29 owns the full semantic alignment evidence layer.
    What is refused here is the one case that is unambiguous at this level --
    the thing under trial is also the evaluator.
    """
    subject = obligation.spec.get("subject")
    return bool(subject) and mechanism.provenance == subject


def compile_obligation_plan(
    obligations: Sequence[RuntimeObligation],
    situation: Situation,
    mechanisms: Iterable[DischargeMechanism] = (),
) -> ObligationPlan:
    """Route each obligation to a discharge path, failing closed where none exists.

    Capability-bearing obligations go to the #13 matcher and **only** those do.
    Everything else is matched to a registered mechanism of the same kind. A
    required before or during obligation with no viable path is a gap.
    """
    by_kind: dict[str, list[DischargeMechanism]] = {}
    for mechanism in mechanisms:
        by_kind.setdefault(mechanism.kind, []).append(mechanism)

    seen: set[str] = set()
    for obligation in obligations:
        if obligation.id in seen:
            raise ObligationError(f"duplicate obligation id: {obligation.id}")
        seen.add(obligation.id)

    gates = [item for item in obligations if item.kind == CAPABILITY_GATE]
    capability_plan = compile_cast_plan(
        {item.id: item.demand for item in gates},
        situation,
    )

    bindings: dict[str, ObligationBinding] = {}
    gaps: list[str] = []

    for obligation in obligations:
        if obligation.kind == CAPABILITY_GATE:
            if obligation.id in capability_plan.matches:
                bindings[obligation.id] = ObligationBinding(
                    obligation, capability_requirement_id=obligation.id
                )
            elif obligation.required and obligation.phase in PRE_CLOSURE_PHASES:
                gaps.append(f"obligation-undischargeable:{obligation.id}:{CAPABILITY_GATE}")
            else:
                bindings[obligation.id] = ObligationBinding(obligation)
            continue

        candidates = [
            mechanism
            for mechanism in by_kind.get(obligation.kind, [])
            if not _self_certifying(obligation, mechanism)
        ]
        if not candidates:
            if obligation.required and obligation.phase in PRE_CLOSURE_PHASES:
                gaps.append(f"obligation-undischargeable:{obligation.id}:{obligation.kind}")
                continue
            bindings[obligation.id] = ObligationBinding(obligation)
            continue
        if len(candidates) > 1:
            named = ",".join(sorted(item.id for item in candidates))
            gaps.append(f"obligation-ambiguous:{obligation.id}:{named}")
            continue
        bindings[obligation.id] = ObligationBinding(obligation, mechanism=candidates[0])

    # A capability gap the matcher reported is a real gap even where the
    # obligation loop above did not restate it.
    gaps.extend(capability_plan.gaps)

    return ObligationPlan(bindings=bindings, gaps=tuple(gaps), capability_plan=capability_plan)


def discharge(
    plan: ObligationPlan,
    context: Mapping[str, Any],
    *,
    phase: str | None = None,
) -> list[ObligationOutcome]:
    """Evaluate obligations and report what each one actually did.

    Four statuses, kept apart because they mean different things:

    - `discharged`   the evidence was produced and satisfies the obligation;
    - `violated`     the evidence was produced and defeats it;
    - `unresolved`   no evidence could be produced;
    - `not_applicable` the obligation does not apply in this Situation.
    """
    outcomes: list[ObligationOutcome] = []
    for binding in plan.bindings.values():
        obligation = binding.obligation
        if phase is not None and obligation.phase != phase:
            continue

        if obligation.kind == CAPABILITY_GATE:
            match = plan.capability_plan.matches.get(obligation.id)
            if match is None:
                status = NOT_APPLICABLE if not obligation.required else UNRESOLVED
                outcomes.append(_outcome(obligation, status, None, None, {}))
                continue
            outcomes.append(
                _outcome(
                    obligation,
                    DISCHARGED,
                    f"capability:{match.receipt.name}",
                    match.receipt.evidence,
                    {"relation": match.relation, "match": dict(match.detail),
                     "attenuated": match.attenuated},
                )
            )
            continue

        mechanism = binding.mechanism
        if mechanism is None:
            status = NOT_APPLICABLE if not obligation.required else UNRESOLVED
            outcomes.append(_outcome(obligation, status, None, None, {}))
            continue

        try:
            result = mechanism.check(obligation, context)
        except Exception as exc:  # a checker that fails is unresolved, not satisfied
            outcomes.append(
                _outcome(
                    obligation, UNRESOLVED, mechanism.id, mechanism.provenance,
                    {"error": f"{type(exc).__name__}: {exc}",
                     "evidence_contract": mechanism.evidence_contract},
                )
            )
            continue

        satisfied, detail = _normalize(result)
        outcomes.append(
            _outcome(
                obligation,
                DISCHARGED if satisfied else VIOLATED,
                mechanism.id,
                mechanism.provenance,
                {**detail, "evidence_contract": mechanism.evidence_contract},
            )
        )
    return outcomes


def _normalize(result: Any) -> tuple[bool, dict[str, Any]]:
    if isinstance(result, tuple) and len(result) == 2:
        satisfied, detail = result
        return bool(satisfied), dict(detail or {})
    return bool(result), {}


def _outcome(
    obligation: RuntimeObligation,
    status: str,
    mechanism_id: str | None,
    provenance: str | None,
    detail: Mapping[str, Any],
) -> ObligationOutcome:
    return ObligationOutcome(
        obligation_id=obligation.id,
        requirement_id=obligation.requirement_id,
        kind=obligation.kind,
        phase=obligation.phase,
        status=status,
        mechanism_id=mechanism_id,
        provenance=provenance,
        detail=dict(detail),
    )
