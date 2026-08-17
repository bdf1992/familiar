"""Observe the Brink and close an exactly attached open CrossingPlan (issue #73).

This Work seam is the last boundary before #16 may move Mana. It composes the
existing #71 open-plan attachment with the existing #34 Brink/Closure contract,
but grants neither execution nor Mana authority itself.

The order is intentional:

    construct exact open plan
    -> retain a non-authorizing construction receipt
    -> verify Situation + open-plan attachment
    -> independently observe Cast-attributable effect/Mana deltas
    -> verify the attachment again after the probes
    -> Closure

The second verification matters because a probe is code. Observation must not
create a write window in which the thing being observed can silently become a
different plan before it is sealed.

`construction_digest` is domain-separated from Closure's `plan_digest`. It is a
local integrity receipt for what #71 constructed, not authorization, provenance,
or a substitute for Closure. `Digest != provenance` remains true.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any

from .crossing import (
    BrinkFinding,
    ClosedPlan,
    CrossingPlan,
    EvidenceContract,
    ManaParticipation,
    ResidualBounds,
    canonical_material,
    close,
    observe_brink,
)
from .handle_situation import situation_evidence_digest
from .obligations import DischargeMechanism, RuntimeObligation
from .situation_crossing import construct_open_crossing_plan


class BrinkClosureError(ValueError):
    """The observed-Brink Closure seam cannot preserve its invariants."""


@dataclass(frozen=True)
class OpenPlanAttachment:
    """Non-authorizing integrity receipt for one #71 open-plan construction.

    The plan remains open. This receipt only lets a later seam notice that the
    open plan or its Situation evidence changed after exact construction.
    """

    plan: CrossingPlan
    situation_evidence_digest: str
    construction_digest: str


@dataclass(frozen=True)
class EnvironmentBrinkProbe:
    """One independent Environment observation used at the Brink."""

    kind: str
    environment: str
    observer: str
    provenance: str
    read: Callable[[], int]

    def __post_init__(self) -> None:
        if self.kind not in {"effect", "mana"}:
            raise BrinkClosureError("Brink probe kind must be effect or mana")
        for name in ("environment", "observer", "provenance"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise BrinkClosureError(f"Brink probe requires {name}")
        if not callable(self.read):
            raise BrinkClosureError("Brink probe read must be callable")


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(value[key]) for key in sorted(value, key=str)}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def open_plan_construction_material(plan: CrossingPlan) -> dict[str, Any]:
    """Material covered by the pre-Closure construction receipt.

    Domain separation ensures this digest is not byte-identical to Closure's
    `plan_digest`, even though both ultimately cover the complete plan material.
    """

    if not isinstance(plan, CrossingPlan):
        raise BrinkClosureError("open-plan construction requires CrossingPlan")
    return {
        "kind": "open-plan-attachment",
        "version": "0.1-work",
        "plan": canonical_material(plan),
    }


def open_plan_construction_digest(plan: CrossingPlan) -> str:
    encoded = json.dumps(
        open_plan_construction_material(plan),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return "sha256:" + sha256(encoded).hexdigest()


def construct_attached_open_plan(
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
) -> OpenPlanAttachment:
    """Construct the #71 plan and immediately retain its integrity receipt."""

    plan = construct_open_crossing_plan(
        situation_view,
        spell=spell,
        technique=technique,
        obligations=obligations,
        mechanisms=mechanisms,
        mana=mana,
        evidence_contracts=evidence_contracts,
        residual_bounds=residual_bounds,
        required_situation_evidence=required_situation_evidence,
    )
    evidence_digest = situation_view.get("situation_evidence_digest")
    if not isinstance(evidence_digest, str) or not evidence_digest:
        raise BrinkClosureError("SituationView requires situation_evidence_digest")
    return OpenPlanAttachment(
        plan=plan,
        situation_evidence_digest=evidence_digest,
        construction_digest=open_plan_construction_digest(plan),
    )


def _require_mapping(name: str, value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise BrinkClosureError(f"{name} must be a mapping")
    return value


def verify_open_plan_attachment(
    attachment: OpenPlanAttachment,
    situation_view: Mapping[str, Any],
) -> None:
    """Prove the open plan is still exactly the #71 product for this Situation.

    This is integrity, not authorization. It refuses stale/tampered local
    material before a Brink observation can be used to seal it.
    """

    if not isinstance(attachment, OpenPlanAttachment):
        raise BrinkClosureError("Closure requires OpenPlanAttachment")
    situation_view = _require_mapping("situation_view", situation_view)

    recorded_situation_digest = situation_view.get("situation_evidence_digest")
    if not isinstance(recorded_situation_digest, str) or not recorded_situation_digest:
        raise BrinkClosureError("SituationView requires situation_evidence_digest")
    actual_situation_digest = situation_evidence_digest(situation_view)
    if recorded_situation_digest != actual_situation_digest:
        raise BrinkClosureError(
            "Situation evidence digest does not match authoritative situated material"
        )
    if attachment.situation_evidence_digest != actual_situation_digest:
        raise BrinkClosureError(
            "open plan is attached to different Situation evidence"
        )

    plan = attachment.plan
    if not plan.ready:
        raise BrinkClosureError("open plan is no longer ready")
    actual_construction_digest = open_plan_construction_digest(plan)
    if attachment.construction_digest != actual_construction_digest:
        raise BrinkClosureError("open-plan construction digest does not match current plan")

    configuration = _require_mapping("plan configuration", plan.configuration)
    plan_situation = _require_mapping("plan situation", configuration.get("situation"))
    view_situation = _require_mapping("SituationView situation", situation_view.get("situation"))
    plan_evidence = _require_mapping(
        "plan Situation evidence", configuration.get("situation_evidence")
    )

    expected_pairs = (
        ("situation id", plan_situation.get("id"), view_situation.get("id")),
        ("session id", plan_situation.get("session_id"), view_situation.get("session_id")),
        ("caster", configuration.get("caster"), view_situation.get("caster")),
        ("target", configuration.get("target"), view_situation.get("target")),
        ("environments", configuration.get("environments"), view_situation.get("environments")),
        ("Situation digest", plan_evidence.get("digest"), actual_situation_digest),
    )
    for name, observed, expected in expected_pairs:
        if _plain(observed) != _plain(expected):
            raise BrinkClosureError(f"open plan {name} no longer matches Situation evidence")


def _validate_probe(
    probe: EnvironmentBrinkProbe | None,
    expected_kind: str,
    plan: CrossingPlan,
) -> None:
    if probe is None:
        return
    if not isinstance(probe, EnvironmentBrinkProbe):
        raise BrinkClosureError(f"{expected_kind} probe must be EnvironmentBrinkProbe")
    if probe.kind != expected_kind:
        raise BrinkClosureError(
            f"{expected_kind} probe declares wrong kind: {probe.kind}"
        )

    configuration = _require_mapping("plan configuration", plan.configuration)
    environments = configuration.get("environments", ())
    if probe.environment not in environments:
        raise BrinkClosureError(
            f"{expected_kind} probe environment is not part of the situated plan"
        )

    caster = configuration.get("caster", {})
    caster_id = caster.get("id") if isinstance(caster, Mapping) else None
    technique = configuration.get("technique", {})
    technique_id = technique.get("id") if isinstance(technique, Mapping) else None
    if probe.observer in {caster_id, technique_id}:
        raise BrinkClosureError(
            f"{expected_kind} Brink observation is not independent of caster/Technique"
        )


def _enrich_brink(
    raw: BrinkFinding,
    effect_probe: EnvironmentBrinkProbe | None,
    mana_probe: EnvironmentBrinkProbe | None,
) -> BrinkFinding:
    probes = {"effect": effect_probe, "mana": mana_probe}
    enriched: list[Mapping[str, Any]] = []
    for observation in raw.observations:
        name = observation.get("probe")
        probe = probes.get(name)
        record = deepcopy(dict(observation))
        if probe is not None:
            record.update(
                {
                    "environment": probe.environment,
                    "observer": probe.observer,
                    "provenance": probe.provenance,
                }
            )
        enriched.append(record)
    return BrinkFinding(
        effect_delta=raw.effect_delta,
        mana_delta=raw.mana_delta,
        observations=tuple(enriched),
        unobservable=raw.unobservable,
    )


def observe_and_close(
    attachment: OpenPlanAttachment,
    situation_view: Mapping[str, Any],
    *,
    effect_probe: EnvironmentBrinkProbe | None,
    mana_probe: EnvironmentBrinkProbe | None,
) -> ClosedPlan:
    """Observe a real Brink and close, without moving Mana or executing.

    Missing or failing probes become unobservable through the existing #34
    contract. Non-zero Cast-attributable deltas also refuse in `close()`.
    """

    verify_open_plan_attachment(attachment, situation_view)
    _validate_probe(effect_probe, "effect", attachment.plan)
    _validate_probe(mana_probe, "mana", attachment.plan)

    raw = observe_brink(
        None if effect_probe is None else effect_probe.read,
        None if mana_probe is None else mana_probe.read,
    )
    brink = _enrich_brink(raw, effect_probe, mana_probe)

    # A probe is code. Re-check after observation so a probe cannot mutate the
    # open plan or Situation and then have that changed material sealed.
    verify_open_plan_attachment(attachment, situation_view)
    return close(attachment.plan, brink)
