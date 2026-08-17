"""Independent post-execution observation/evaluation seam for issue #35.

The Environment records raw evidence. This module evaluates that evidence on
Cast's terms: against the exact Runtime Obligations, DischargeMechanisms, and
EvidenceContracts frozen inside one immutable ClosedPlan.

It deliberately keeps five things separate:

    executor claim
    raw Environment observations
    obligation evaluation findings
    world consequence finding
    Mana settlement decision

The executor claim is retained even when independent observation disagrees.
Unknown/unavailable evidence is retained and never converted into false/zero.
Multiple independent observers may disagree; disagreement yields `unresolved`
rather than last-writer-wins.

The account produced here is evidence for #36 to seal later. It is not CAST.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field, is_dataclass
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence

from environment.consequence import ConsequenceFinding
from environment.magic import ConsequenceDecision, MagicRuntimeError
from environment.observation import (
    OBSERVED,
    UNKNOWN,
    UNAVAILABLE,
    EnvironmentObservation,
    observer_is_independent,
)

from .crossing import ClosedPlan, EvidenceContract
from .obligations import (
    NOT_APPLICABLE,
    SATISFIED,
    UNRESOLVED,
    VIOLATED,
    RuntimeObligation,
)


class ObservationEvaluationError(ValueError):
    """Post-execution evidence cannot be bound to the sealed Cast contract."""


@dataclass(frozen=True)
class ExecutorClaim:
    """What the executor says happened. A claim, never consequence truth."""

    succeeded: bool
    result: Any = None
    error_type: str | None = None
    error_message: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "succeeded": self.succeeded,
            "result": deepcopy(self.result),
            "error_type": self.error_type,
            "error_message": self.error_message,
        }


@dataclass(frozen=True)
class ObligationObservationFinding:
    """Evaluation of one after-phase obligation against its sealed standard."""

    obligation_id: str
    requirement_id: str
    evidence_contract: Mapping[str, Any]
    evaluator_id: str | None
    evaluator_provenance: str | None
    observation_ids: tuple[str, ...]
    status: str
    detail: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "obligation_id": self.obligation_id,
            "requirement_id": self.requirement_id,
            "evidence_contract": deepcopy(dict(self.evidence_contract)),
            "evaluator_id": self.evaluator_id,
            "evaluator_provenance": self.evaluator_provenance,
            "observation_ids": list(self.observation_ids),
            "status": self.status,
            "detail": deepcopy(dict(self.detail)),
        }


@dataclass(frozen=True)
class CrossingObservationAccount:
    """One attributable post-execution observation account for one ClosedPlan."""

    cast_id: str
    plan_digest: str
    executor_claim: ExecutorClaim
    observations: tuple[EnvironmentObservation, ...]
    obligation_findings: tuple[ObligationObservationFinding, ...]
    consequence: Mapping[str, Any]
    unknown: tuple[str, ...]
    digest: str

    def material(self) -> dict[str, Any]:
        return {
            "cast_id": self.cast_id,
            "plan_digest": self.plan_digest,
            "executor_claim": self.executor_claim.as_dict(),
            "observations": [item.as_dict() for item in self.observations],
            "obligation_findings": [item.as_dict() for item in self.obligation_findings],
            "consequence": deepcopy(dict(self.consequence)),
            "unknown": list(self.unknown),
        }


def _canonical_digest(material: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        material, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str
    ).encode("utf-8")
    return "sha256:" + sha256(encoded).hexdigest()


def _contract_material(contract: EvidenceContract | None) -> dict[str, Any]:
    if contract is None:
        return {}
    return contract.as_material()


def _consequence_material(finding: ConsequenceFinding) -> dict[str, Any]:
    if not isinstance(finding, ConsequenceFinding):
        raise ObservationEvaluationError("consequence must be ConsequenceFinding")
    if not is_dataclass(finding):
        raise ObservationEvaluationError("ConsequenceFinding must remain a dataclass value")
    return deepcopy(asdict(finding))


def _principals(closed: ClosedPlan, mana_participant: str | None) -> tuple[str | None, ...]:
    configuration = closed.plan.configuration
    caster = configuration.get("caster", {}) if isinstance(configuration, Mapping) else {}
    technique = configuration.get("technique", {}) if isinstance(configuration, Mapping) else {}
    caster_id = caster.get("id") if isinstance(caster, Mapping) else None
    technique_id = technique.get("id") if isinstance(technique, Mapping) else None
    return caster_id, technique_id, mana_participant


def _after_obligations(closed: ClosedPlan) -> tuple[tuple[RuntimeObligation, Any], ...]:
    out: list[tuple[RuntimeObligation, Any]] = []
    for binding in closed.plan.obligations.bindings.values():
        if binding.obligation.phase == "after":
            out.append((binding.obligation, binding))
    return tuple(sorted(out, key=lambda item: item[0].id))


def _evaluate_one(
    closed: ClosedPlan,
    obligation: RuntimeObligation,
    binding: Any,
    observations: Sequence[EnvironmentObservation],
    context: Mapping[str, Any],
    principals: tuple[str | None, ...],
) -> ObligationObservationFinding:
    contract = closed.plan.evidence_contract_for(obligation.id)
    if obligation.required and contract is None:
        raise ObservationEvaluationError(
            f"required after obligation has no sealed evidence contract: {obligation.id}"
        )

    mechanism = binding.mechanism
    if mechanism is None:
        status = NOT_APPLICABLE if not obligation.required else UNRESOLVED
        return ObligationObservationFinding(
            obligation_id=obligation.id,
            requirement_id=obligation.requirement_id,
            evidence_contract=_contract_material(contract),
            evaluator_id=None,
            evaluator_provenance=None,
            observation_ids=(),
            status=status,
            detail={"reason": "no evaluator mechanism"},
        )

    if contract is None:
        # Optional obligations may be evaluable, but no standard was sealed.
        # Treat that as not applicable rather than inventing a post-hoc standard.
        return ObligationObservationFinding(
            obligation_id=obligation.id,
            requirement_id=obligation.requirement_id,
            evidence_contract={},
            evaluator_id=mechanism.id,
            evaluator_provenance=mechanism.provenance,
            observation_ids=(),
            status=NOT_APPLICABLE,
            detail={"reason": "no sealed evidence contract"},
        )

    if contract.observer != mechanism.provenance:
        raise ObservationEvaluationError(
            f"sealed evidence evaluator mismatch for {obligation.id}: "
            f"contract={contract.observer} mechanism={mechanism.provenance}"
        )

    addressed = tuple(
        observation
        for observation in observations
        if observation.cast_id == context["cast_id"] and observation.topic == obligation.id
    )
    independent = tuple(
        observation
        for observation in addressed
        if observer_is_independent(observation.observer, *principals)
    )
    rejected = tuple(item.id for item in addressed if item not in independent)
    explicit_unknown = tuple(
        item.id for item in independent if item.status in {UNKNOWN, UNAVAILABLE}
    )
    observed = tuple(item for item in independent if item.status == OBSERVED)

    if not observed:
        return ObligationObservationFinding(
            obligation_id=obligation.id,
            requirement_id=obligation.requirement_id,
            evidence_contract=_contract_material(contract),
            evaluator_id=mechanism.id,
            evaluator_provenance=mechanism.provenance,
            observation_ids=tuple(item.id for item in addressed),
            status=UNRESOLVED,
            detail={
                "reason": "no independent observed value",
                "unknown_or_unavailable": list(explicit_unknown),
                "self_observation_rejected": list(rejected),
            },
        )

    evaluated: list[dict[str, Any]] = []
    outcomes: list[bool] = []
    for observation in observed:
        evaluation_context = dict(context)
        evaluation_context.update(
            {
                "observation": observation.as_dict(),
                "observation_value": deepcopy(observation.value),
                "raw_observations": tuple(item.as_dict() for item in addressed),
            }
        )
        try:
            passed = bool(mechanism.check(obligation, evaluation_context))
        except Exception as error:  # noqa: BLE001 -- failed evaluator means unresolved
            evaluated.append(
                {
                    "observation_id": observation.id,
                    "status": UNRESOLVED,
                    "error": f"{type(error).__name__}: {error}",
                }
            )
            continue
        outcomes.append(passed)
        evaluated.append(
            {
                "observation_id": observation.id,
                "status": SATISFIED if passed else VIOLATED,
            }
        )

    if len(outcomes) != len(observed):
        status = UNRESOLVED
        reason = "evaluator failed for at least one independent observation"
    elif all(outcomes):
        status = SATISFIED
        reason = "all independent observed values satisfy the sealed evaluator"
    elif not any(outcomes):
        status = VIOLATED
        reason = "all independent observed values violate the sealed evaluator"
    else:
        status = UNRESOLVED
        reason = "independent observers disagree"

    return ObligationObservationFinding(
        obligation_id=obligation.id,
        requirement_id=obligation.requirement_id,
        evidence_contract=_contract_material(contract),
        evaluator_id=mechanism.id,
        evaluator_provenance=mechanism.provenance,
        observation_ids=tuple(item.id for item in addressed),
        status=status,
        detail={
            "reason": reason,
            "evaluations": evaluated,
            "unknown_or_unavailable": list(explicit_unknown),
            "self_observation_rejected": list(rejected),
        },
    )


def evaluate_crossing_observations(
    closed: ClosedPlan,
    cast_id: str,
    *,
    executor_claim: ExecutorClaim,
    observations: Sequence[EnvironmentObservation],
    consequence: ConsequenceFinding,
    context: Mapping[str, Any] | None = None,
    mana_participant: str | None = None,
) -> CrossingObservationAccount:
    """Evaluate post-execution evidence against the exact sealed ClosedPlan.

    The consequence is already an Environment-owned finding from #27. This
    function verifies its observer is independent from caster/Technique/Mana
    participant, records it beside (not instead of) the executor claim, and
    evaluates every after-phase obligation from raw Environment observations.
    """

    if not isinstance(closed, ClosedPlan):
        raise ObservationEvaluationError("evaluation requires ClosedPlan")
    if not isinstance(cast_id, str) or not cast_id:
        raise ObservationEvaluationError("cast_id must be a non-empty string")
    if not isinstance(executor_claim, ExecutorClaim):
        raise ObservationEvaluationError("executor_claim must be ExecutorClaim")
    if not all(isinstance(item, EnvironmentObservation) for item in observations):
        raise ObservationEvaluationError("observations must be EnvironmentObservation values")

    wrong_cast = [item.id for item in observations if item.cast_id != cast_id]
    if wrong_cast:
        raise ObservationEvaluationError(
            "observation belongs to another Cast: " + ", ".join(wrong_cast)
        )

    principals = _principals(closed, mana_participant)
    consequence_material = _consequence_material(consequence)
    consequence_observer = consequence_material.get("observer")
    if not observer_is_independent(consequence_observer, *principals):
        raise ObservationEvaluationError(
            "consequence observer is not independent of caster/Technique/Mana participant"
        )

    base_context = dict(context or {})
    base_context.update(
        {
            "cast_id": cast_id,
            "closed_plan_digest": closed.digest,
            "configuration": deepcopy(closed.plan.configuration),
        }
    )

    findings = tuple(
        _evaluate_one(closed, obligation, binding, observations, base_context, principals)
        for obligation, binding in _after_obligations(closed)
    )

    unknown = tuple(
        sorted(
            {
                *(item.id for item in observations if item.status in {UNKNOWN, UNAVAILABLE}),
                *(item.obligation_id for item in findings if item.status == UNRESOLVED),
            }
        )
    )

    material = {
        "cast_id": cast_id,
        "plan_digest": closed.digest,
        "executor_claim": executor_claim.as_dict(),
        "observations": [item.as_dict() for item in observations],
        "obligation_findings": [item.as_dict() for item in findings],
        "consequence": consequence_material,
        "unknown": list(unknown),
    }
    return CrossingObservationAccount(
        cast_id=cast_id,
        plan_digest=closed.digest,
        executor_claim=executor_claim,
        observations=tuple(deepcopy(tuple(observations))),
        obligation_findings=findings,
        consequence=consequence_material,
        unknown=unknown,
        digest=_canonical_digest(material),
    )


class ObservationAccountStore:
    """Append-only per-Cast evaluated accounts plus a Magic verifier adapter."""

    def __init__(self) -> None:
        self._accounts: dict[str, CrossingObservationAccount] = {}

    def put(self, account: CrossingObservationAccount) -> None:
        if not isinstance(account, CrossingObservationAccount):
            raise ObservationEvaluationError("store accepts CrossingObservationAccount")
        existing = self._accounts.get(account.cast_id)
        if existing is not None:
            if existing.digest == account.digest:
                return
            raise ObservationEvaluationError(
                f"observation account already exists for Cast: {account.cast_id}"
            )
        self._accounts[account.cast_id] = account

    def get(self, cast_id: str) -> CrossingObservationAccount | None:
        return self._accounts.get(cast_id)

    def consequence_decision(self, cast_id: str, commitment: Mapping[str, Any]) -> ConsequenceDecision:
        """Adapt the broad #35 account into Magic's narrow settlement decision.

        Spending is read from independently observed consequence detail, never
        from executor success/failure. `mana_spent` must be explicit because a
        consequence kind is not itself a scalar Mana contraction.
        """

        account = self._accounts.get(cast_id)
        if account is None:
            raise MagicRuntimeError(f"no evaluated observation account for Cast: {cast_id}")
        amount = commitment.get("amount")
        if not isinstance(amount, int) or isinstance(amount, bool) or amount < 0:
            raise MagicRuntimeError("commitment amount is not a non-negative integer")

        detail = account.consequence.get("detail", {})
        if not isinstance(detail, Mapping):
            raise MagicRuntimeError("evaluated consequence detail is malformed")
        spent = detail.get("mana_spent")
        if not isinstance(spent, int) or isinstance(spent, bool) or spent < 0:
            raise MagicRuntimeError("evaluated consequence does not state integer mana_spent")
        if spent > amount:
            raise MagicRuntimeError(
                f"evaluated consequence spends {spent} above committed {amount}"
            )

        observer = account.consequence.get("observer")
        if not isinstance(observer, str) or not observer:
            raise MagicRuntimeError("evaluated consequence has no observer identity")
        return ConsequenceDecision(
            confirmed=True,
            spent=spent,
            observer=observer,
            receipt_id=f"observation-account:{account.digest}",
            reason="settlement derived from evaluated independent crossing observation",
        )

    @property
    def accounts(self) -> tuple[CrossingObservationAccount, ...]:
        return tuple(self._accounts[key] for key in sorted(self._accounts))
