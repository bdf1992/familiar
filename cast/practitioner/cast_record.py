"""Immutable CAST record sealing Work for issue #36.

A CAST record is an attributable account of one crossing attempt. It is not the
crossing, not truth, not a signature, and not Effect standing.

The integrity boundary is deliberately stronger than a frozen dataclass holding
mutable dictionaries: `SealedCastRecord` stores canonical JSON text as its
material state. Every read reparses that text, so mutation of caller-owned input
or a returned materialization cannot rewrite the seal.

`record_digest` identifies those exact canonical record bytes. External signer
provenance/attestation remains the separate Registry contract from #31.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, is_dataclass
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence

from environment.magic import ManaEvent

from .crossing import ClosedPlan, canonical_material, plan_digest
from .obligations import UNRESOLVED, VIOLATED
from .observation import CrossingObservationAccount


CAST_RECORD_VERSION = "0.7-draft"
CAST_STATUSES = frozenset({"successful", "refused", "aborted", "violated", "unresolved"})


class CastSealingError(ValueError):
    """Crossing evidence cannot be faithfully sealed into one CAST record."""


def _plain(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _plain(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _plain(value[key]) for key in sorted(value, key=str)}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise CastSealingError(f"CAST material is not JSON-representable: {type(value).__name__}")


def canonical_record_material(material: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize exactly the material covered by `record_digest`.

    `record_digest` itself is excluded to avoid a recursive identity. Lists keep
    their order because Mana/event/execution ordering is evidence. Mapping key
    order is normalized.
    """

    if not isinstance(material, Mapping):
        raise CastSealingError("CAST material must be a mapping")
    normalized = _plain({key: value for key, value in material.items() if key != "record_digest"})
    if normalized.get("cast_format") != CAST_RECORD_VERSION:
        raise CastSealingError(f"cast_format must be {CAST_RECORD_VERSION}")
    cast_id = normalized.get("cast_id")
    if not isinstance(cast_id, str) or not cast_id:
        raise CastSealingError("CAST requires cast_id")
    status = normalized.get("status")
    if status not in CAST_STATUSES:
        raise CastSealingError(f"unsupported CAST status: {status!r}")
    plan = normalized.get("plan_digest")
    if status == "refused":
        if plan is not None:
            raise CastSealingError("a pre-Closure refusal must not claim a plan_digest")
    elif not isinstance(plan, str) or not plan.startswith("sha256:"):
        raise CastSealingError("a post-Closure CAST requires plan_digest")
    return normalized


def record_digest(material: Mapping[str, Any]) -> str:
    canonical = canonical_record_material(material)
    encoded = json.dumps(
        canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return "sha256:" + sha256(encoded).hexdigest()


@dataclass(frozen=True)
class SealedCastRecord:
    """One immutable canonical CAST account plus its content identity."""

    _canonical_json: str
    record_digest: str

    def material(self) -> dict[str, Any]:
        material = json.loads(self._canonical_json)
        material["record_digest"] = self.record_digest
        return material

    def canonical_material(self) -> dict[str, Any]:
        return json.loads(self._canonical_json)


def seal_cast(material: Mapping[str, Any]) -> SealedCastRecord:
    canonical = canonical_record_material(material)
    encoded = json.dumps(
        canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    digest = "sha256:" + sha256(encoded.encode("utf-8")).hexdigest()
    return SealedCastRecord(encoded, digest)


def _mana_event_material(event: ManaEvent) -> dict[str, Any]:
    if not isinstance(event, ManaEvent):
        raise CastSealingError("mana_transitions must contain ManaEvent values")
    return _plain(asdict(event))


def _event_cast_id(event: ManaEvent) -> str | None:
    value = event.details.get("cast_id")
    return value if isinstance(value, str) else None


def _derive_status(account: CrossingObservationAccount) -> str:
    statuses = {finding.status for finding in account.obligation_findings}
    if VIOLATED in statuses:
        return "violated"
    if UNRESOLVED in statuses or account.unknown:
        return "unresolved"
    if not account.executor_claim.succeeded:
        return "aborted"
    return "successful"


def seal_crossing(
    closed: ClosedPlan,
    account: CrossingObservationAccount,
    *,
    mana_events: Sequence[ManaEvent] = (),
    residuals: Sequence[Mapping[str, Any]] = (),
    execution_trace: Sequence[Mapping[str, Any]] = (),
) -> SealedCastRecord:
    """Seal one post-Closure crossing from already-attributable evidence.

    This function does not execute, observe, settle, attest, or decide trust. It
    verifies exact identity relations among existing evidence and records them.
    """

    if not isinstance(closed, ClosedPlan):
        raise CastSealingError("sealing a crossing requires ClosedPlan")
    if not isinstance(account, CrossingObservationAccount):
        raise CastSealingError("sealing a crossing requires CrossingObservationAccount")
    actual_plan_digest = plan_digest(closed.plan)
    if closed.digest != actual_plan_digest:
        raise CastSealingError("ClosedPlan digest no longer matches its immutable material")
    if account.plan_digest != closed.digest:
        raise CastSealingError("observation account belongs to another ClosedPlan")

    events = tuple(mana_events)
    for event in events:
        if not isinstance(event, ManaEvent):
            raise CastSealingError("mana_transitions must contain ManaEvent values")
        event_cast_id = _event_cast_id(event)
        if event.operation in {"commit", "settle"} and event_cast_id != account.cast_id:
            raise CastSealingError("Mana transition belongs to another Cast")

    plan_material = canonical_material(closed.plan)
    capacity = deepcopy(plan_material["capacity"])
    enforced_handles = {
        requirement_id: deepcopy(match["handle"])
        for requirement_id, match in capacity.items()
    }
    event_material = [_mana_event_material(event) for event in events]
    settlement = next(
        (deepcopy(item) for item in reversed(event_material) if item.get("operation") == "settle"),
        None,
    )

    material = {
        "cast_format": CAST_RECORD_VERSION,
        "cast_id": account.cast_id,
        "plan_digest": closed.digest,
        "recorded_configuration": deepcopy(plan_material["configuration"]),
        "capability_match_evidence": capacity,
        "enforced_handle_receipts": enforced_handles,
        "mana_transitions": event_material,
        "obligation_findings": [finding.as_dict() for finding in account.obligation_findings],
        "observations": [observation.as_dict() for observation in account.observations],
        "execution_trace": {
            "executor_claim": account.executor_claim.as_dict(),
            "events": _plain(tuple(execution_trace)),
        },
        "outcome": {
            "consequence": deepcopy(dict(account.consequence)),
            "unknown": list(account.unknown),
        },
        "residuals": _plain(tuple(residuals)),
        "mana_settlement": settlement,
        "status": _derive_status(account),
    }
    return seal_cast(material)


def seal_refusal(
    cast_id: str,
    *,
    recorded_configuration: Mapping[str, Any],
    refusal_reasons: Sequence[str],
    observations: Sequence[Mapping[str, Any]] = (),
) -> SealedCastRecord:
    """Seal a pre-Closure refusal without pretending a ClosedPlan existed."""

    reasons = tuple(refusal_reasons)
    if not reasons or not all(isinstance(reason, str) and reason for reason in reasons):
        raise CastSealingError("a refusal record requires one or more named reasons")
    return seal_cast(
        {
            "cast_format": CAST_RECORD_VERSION,
            "cast_id": cast_id,
            "plan_digest": None,
            "recorded_configuration": deepcopy(dict(recorded_configuration)),
            "capability_match_evidence": {},
            "enforced_handle_receipts": {},
            "mana_transitions": [],
            "obligation_findings": [],
            "observations": _plain(tuple(observations)),
            "execution_trace": {"attempted": False, "events": []},
            "outcome": {"refusal_reasons": list(reasons)},
            "residuals": [],
            "mana_settlement": None,
            "status": "refused",
        }
    )
