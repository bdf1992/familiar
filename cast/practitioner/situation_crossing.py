"""Attach #69 Situation evidence to the existing #34 CrossingPlan contract.

This is deliberately pre-Closure Work. It constructs one *open* CrossingPlan
from an integrity-checked SituationView and the already-proven obligation /
capacity machinery. It never observes the Brink, calls `close`, computes a
closed plan digest, moves Mana, executes a Technique, mutates Environment state,
or creates CAST.

The critical attachment law is:

    exact Demand + exact Environment receipt + exact attenuated handle
        in Situation evidence
    ==
    exact capability binding carried by the CrossingPlan

If that equality does not hold, construction refuses rather than re-resolving
from Context, Familiarity, an operation name, or a broader capability.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
from typing import Any, Iterable, Mapping, Sequence

from .crossing import CrossingPlan, EvidenceContract, ManaParticipation, ResidualBounds
from .handle_situation import situation_evidence_digest
from .obligations import (
    CAPABILITY_GATE,
    DischargeMechanism,
    RuntimeObligation,
    compile_obligation_plan,
)
from .situation import CapabilityReceipt, Demand, Situation


class SituationCrossingError(ValueError):
    """Situation evidence cannot be faithfully attached to an open plan."""


_ACCEPTABLE_REQUIRED_RESULTS = frozenset({"confirmed", "confirmed-absent"})


def _mapping(name: str, value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise SituationCrossingError(f"{name} must be a mapping")
    return value


def _text(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise SituationCrossingError(f"{name} must be a non-empty string")
    return value


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(value[key]) for key in sorted(value, key=str)}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _receipt_from_snapshot(raw: Mapping[str, Any]) -> CapabilityReceipt:
    raw = _mapping("capability receipt snapshot", raw)
    operations = raw.get("operations")
    if not isinstance(operations, (list, tuple)) or not all(
        isinstance(item, str) and item for item in operations
    ):
        raise SituationCrossingError("receipt operations must be non-empty strings")
    capacity = raw.get("capacity", {})
    capacity = _mapping("receipt capacity", capacity)

    return CapabilityReceipt(
        name=_text("receipt name", raw.get("name")),
        environment=_text("receipt environment", raw.get("environment")),
        operations=tuple(operations),
        status=_text("receipt status", raw.get("status")),
        authority=_text("receipt authority", raw.get("authority")),
        locator=_text("receipt locator", raw.get("locator")),
        evidence=_text("receipt evidence", raw.get("evidence")),
        protocol=raw.get("protocol"),
        subject=raw.get("subject"),
        capacity=deepcopy(dict(capacity)),
    )


def _receipt_snapshot(receipt: CapabilityReceipt) -> dict[str, Any]:
    result = asdict(receipt)
    result["capacity"] = deepcopy(dict(receipt.capacity))
    return result


def _demand_snapshot(demand: Demand) -> dict[str, Any]:
    return {
        "operation": demand.operation,
        "relation": demand.relation,
        "capability": demand.capability,
        "protocol": demand.protocol,
        "environment": demand.environment,
        "authority": demand.authority,
        "subject": demand.subject,
        "locator": demand.locator,
        "capacity": deepcopy(dict(demand.capacity)),
        "attenuate": demand.attenuate,
    }


def _match_snapshot(match: Any) -> dict[str, Any]:
    return {
        "requirement_id": match.requirement_id,
        "demand": _demand_snapshot(match.demand),
        "relation": match.relation,
        "detail": deepcopy(dict(match.detail)),
        "receipt": _receipt_snapshot(match.receipt),
        "handle": _receipt_snapshot(match.handle),
        "attenuated": match.attenuated,
    }


def _verify_situation_digest(view: Mapping[str, Any]) -> str:
    recorded = _text("situation_evidence_digest", view.get("situation_evidence_digest"))
    actual = situation_evidence_digest(view)
    if recorded != actual:
        raise SituationCrossingError(
            "Situation evidence digest does not match authoritative situated material"
        )
    return recorded


def _required_evidence(
    view: Mapping[str, Any], required_ids: Sequence[str]
) -> tuple[dict[str, Any], ...]:
    comparisons = view.get("comparisons")
    if not isinstance(comparisons, list):
        raise SituationCrossingError("SituationView comparisons must be a list")
    by_id: dict[str, Mapping[str, Any]] = {}
    for raw in comparisons:
        comparison = _mapping("Situation comparison", raw)
        comparison_id = _text("comparison id", comparison.get("id"))
        if comparison_id in by_id:
            raise SituationCrossingError(f"duplicate Situation comparison: {comparison_id}")
        by_id[comparison_id] = comparison

    selected: list[dict[str, Any]] = []
    for evidence_id in required_ids:
        _text("required Situation evidence id", evidence_id)
        comparison = by_id.get(evidence_id)
        if comparison is None:
            raise SituationCrossingError(
                f"required Situation evidence is missing: {evidence_id}"
            )
        result = comparison.get("result")
        if result not in _ACCEPTABLE_REQUIRED_RESULTS:
            raise SituationCrossingError(
                f"required Situation evidence is unresolved: {evidence_id}:{result}"
            )
        selected.append(deepcopy(dict(comparison)))
    return tuple(selected)


def _situation_from_view(view: Mapping[str, Any]) -> Situation:
    raw_situation = _mapping("SituationView situation", view.get("situation"))
    raw_environment = _mapping("SituationView environment", view.get("environment"))

    receipts_raw = raw_environment.get("capability_receipts")
    if not isinstance(receipts_raw, list):
        raise SituationCrossingError("Environment capability_receipts must be a list")
    receipts = tuple(_receipt_from_snapshot(_mapping("receipt", item)) for item in receipts_raw)

    observations = _mapping(
        "Environment observations", raw_environment.get("observations", {})
    )
    caster = _mapping("Situation caster", raw_situation.get("caster"))
    if "target" not in raw_situation:
        raise SituationCrossingError("Situation requires target")
    environments = raw_situation.get("environments", ())
    if not isinstance(environments, (list, tuple)) or not all(
        isinstance(item, str) and item for item in environments
    ):
        raise SituationCrossingError("Situation environments must be strings")

    return Situation(
        id=_text("Situation id", raw_situation.get("id")),
        session_id=_text("Situation session_id", raw_situation.get("session_id")),
        caster=deepcopy(dict(caster)),
        target=deepcopy(raw_situation["target"]),
        environments=tuple(environments),
        capabilities=receipts,
        observations=deepcopy(dict(observations)),
    )


def _verify_capability_attachment(
    view: Mapping[str, Any],
    obligations: Sequence[RuntimeObligation],
    obligation_plan: Any,
) -> None:
    matching = _mapping("Situation capability_matching", view.get("capability_matching"))
    if matching.get("ready") is not True or matching.get("gaps") not in ([], ()):
        raise SituationCrossingError(
            "Situation capability matching is not ready; unresolved evidence is not permission"
        )
    recorded_matches = _mapping("Situation capability matches", matching.get("matches"))

    for obligation in obligations:
        if obligation.kind != CAPABILITY_GATE:
            continue
        recorded = recorded_matches.get(obligation.id)
        if recorded is None:
            raise SituationCrossingError(
                f"capability gate {obligation.id} was not matched by the evidenced Situation"
            )
        compiled = obligation_plan.capability_plan.matches.get(obligation.id)
        if compiled is None:
            raise SituationCrossingError(
                f"capability gate {obligation.id} cannot be reproduced from exact Environment receipts"
            )
        if _plain(recorded) != _plain(_match_snapshot(compiled)):
            raise SituationCrossingError(
                f"capability gate {obligation.id} does not match evidenced Situation binding"
            )


def construct_open_crossing_plan(
    situation_view: Mapping[str, Any],
    *,
    spell: Mapping[str, Any],
    technique: Mapping[str, Any],
    obligations: Sequence[RuntimeObligation],
    mechanisms: Iterable[DischargeMechanism] = (),
    mana: Sequence[ManaParticipation] = (),
    evidence_contracts: Sequence[EvidenceContract] = (),
    residual_bounds: ResidualBounds,
    required_situation_evidence: Sequence[str] = (),
) -> CrossingPlan:
    """Construct one ready, **open** CrossingPlan from exact Situation evidence.

    No Closure occurs here. A caller receives the ordinary #34 `CrossingPlan`,
    which has no digest or Brink until some later owner explicitly performs
    those steps.
    """

    situation_view = _mapping("situation_view", situation_view)
    if situation_view.get("effectful") is not False:
        raise SituationCrossingError("SituationView must be explicitly non-effectful")
    if situation_view.get("runtime_authority") not in ([], ()):
        raise SituationCrossingError("SituationView cannot carry runtime authority")

    evidence_digest = _verify_situation_digest(situation_view)
    required_evidence = _required_evidence(
        situation_view, tuple(required_situation_evidence)
    )

    spell = _mapping("spell selection", spell)
    technique = _mapping("technique selection", technique)
    spell_id = _text("spell id", spell.get("id"))
    technique_id = _text("technique id", technique.get("id"))

    obligations = tuple(obligations)
    if not all(isinstance(item, RuntimeObligation) for item in obligations):
        raise SituationCrossingError("obligations must be RuntimeObligation values")
    mechanisms = tuple(mechanisms)
    if not all(isinstance(item, DischargeMechanism) for item in mechanisms):
        raise SituationCrossingError("mechanisms must be DischargeMechanism values")
    mana = tuple(mana)
    if not all(isinstance(item, ManaParticipation) for item in mana):
        raise SituationCrossingError("mana must be declarative ManaParticipation values")
    evidence_contracts = tuple(evidence_contracts)
    if not all(isinstance(item, EvidenceContract) for item in evidence_contracts):
        raise SituationCrossingError("evidence_contracts must be EvidenceContract values")
    if not isinstance(residual_bounds, ResidualBounds):
        raise SituationCrossingError("residual_bounds must be explicit ResidualBounds")

    situation = _situation_from_view(situation_view)
    obligation_plan = compile_obligation_plan(obligations, situation, mechanisms)
    _verify_capability_attachment(situation_view, obligations, obligation_plan)

    if not obligation_plan.ready:
        raise SituationCrossingError(
            "obligation plan is not ready: " + "; ".join(obligation_plan.gaps)
        )

    configuration = {
        "situation": {
            "id": situation.id,
            "session_id": situation.session_id,
        },
        "caster": deepcopy(situation.caster),
        "target": deepcopy(situation.target),
        "environments": list(situation.environments),
        "spell": {**deepcopy(dict(spell)), "id": spell_id},
        "technique": {**deepcopy(dict(technique)), "id": technique_id},
        "situation_evidence": {
            "digest": evidence_digest,
            "required": [item["id"] for item in required_evidence],
            "drift": [
                {"id": item.get("id"), "result": item.get("result")}
                for item in situation_view.get("drift", [])
            ],
            "uncertain": [
                {"id": item.get("id"), "result": item.get("result")}
                for item in situation_view.get("uncertain", [])
            ],
        },
    }

    plan = CrossingPlan(
        configuration=configuration,
        obligations=obligation_plan,
        mana=mana,
        evidence_contracts=evidence_contracts,
        residual_bounds=residual_bounds,
    )
    if not plan.ready:
        raise SituationCrossingError(
            "constructed CrossingPlan is not ready: " + "; ".join(plan.gaps)
        )
    return plan
