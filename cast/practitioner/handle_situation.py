"""Resolve a read-only Domain Handle against Environment evidence (issue #69).

This Work seam sits between knowledge-side orientation and the existing
Situation capability matcher. It deliberately does not Cast, close a
CrossingPlan, move Mana, execute a Technique, persist state, or mutate an
Environment.

The load-bearing distinction is that Handle claims are not capability evidence.
Concrete capability matching is delegated unchanged to `situation.py` using
`Demand`, `CapabilityReceipt`, and `compile_cast_plan`.

Missing chart material is never inferred to mean absence. Each selected charted
expectation must explicitly say whether its side is present, absent, or unknown.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping, Sequence

from .situation import CapabilityReceipt, Demand, Situation, compile_cast_plan


class HandleSituationError(ValueError):
    """The read-only situation-resolution inputs are malformed or unsafe."""


_MISSING = object()
_OBSERVATION_STATUSES = frozenset({"present", "absent", "unobservable"})
_CHARTED_STATUSES = frozenset({"present", "absent", "unknown"})
_CHANGE_KINDS = {
    "anchor": "stale-anchor",
    "identity": "changed-identity",
    "capacity": "changed-capacity",
    "value": "changed-value",
}
_DRIFT_KINDS = frozenset(
    {
        "charted-present/runtime-absent",
        "charted-absent/runtime-present",
        "stale-anchor",
        "changed-identity",
        "changed-capacity",
        "changed-value",
    }
)


def _require_mapping(name: str, value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise HandleSituationError(f"{name} must be a mapping")
    return value


def _require_text(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise HandleSituationError(f"{name} must be a non-empty string")
    return value


def _canonical_digest(value: Mapping[str, Any]) -> str:
    material = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + sha256(material.encode("utf-8")).hexdigest()


def _verify_handle_sources(handle_view: Mapping[str, Any]) -> Mapping[str, Any]:
    """Fail closed if the Handle source material no longer matches its labels."""

    sources = _require_mapping("handle_view sources", handle_view.get("sources"))
    source_pairs = (
        ("context", "context"),
        ("domain_familiarity", "domain_familiarity"),
    )
    anchors: list[str] = []

    for source_key, material_key in source_pairs:
        source = _require_mapping(f"{source_key} source", sources.get(source_key))
        material = _require_mapping(f"handle_view {material_key}", handle_view.get(material_key))
        identity = _require_mapping(f"{material_key} identity", material.get("identity"))

        source_id = _require_text(f"{source_key} source id", source.get("id"))
        source_anchor = _require_text(f"{source_key} source anchor", source.get("anchor"))
        source_digest = _require_text(f"{source_key} source digest", source.get("digest"))
        material_id = _require_text(f"{material_key} identity id", identity.get("id"))
        material_anchor = _require_text(
            f"{material_key} identity anchor", identity.get("anchor")
        )

        if source_id != material_id or source_anchor != material_anchor:
            raise HandleSituationError(
                f"{source_key} source identity does not match Handle material"
            )
        actual_digest = _canonical_digest(material)
        if source_digest != actual_digest:
            raise HandleSituationError(
                f"{source_key} source digest does not match Handle material"
            )
        anchors.append(source_anchor)

    if len(set(anchors)) != 1:
        raise HandleSituationError(
            "Context and Domain Familiarity must retain the same source anchor"
        )
    return sources


def _at_path(root: Any, path: Sequence[Any]) -> Any:
    """Resolve one explicitly selected Handle path without guessing.

    A missing path returns `_MISSING`; callers decide whether that is malformed
    or expected. It is never silently reinterpreted as a claim of absence.
    """

    current = root
    for segment in path:
        if isinstance(current, Mapping) and isinstance(segment, str):
            if segment not in current:
                return _MISSING
            current = current[segment]
            continue
        if (
            isinstance(current, Sequence)
            and not isinstance(current, (str, bytes, bytearray))
            and isinstance(segment, int)
        ):
            if segment < 0 or segment >= len(current):
                return _MISSING
            current = current[segment]
            continue
        return _MISSING
    return current


def _normalize_observations(value: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    observations: dict[str, dict[str, Any]] = {}
    for observation_id, raw in value.items():
        _require_text("observation id", observation_id)
        observation = _require_mapping(f"observation {observation_id}", raw)
        status = observation.get("status")
        if status not in _OBSERVATION_STATUSES:
            raise HandleSituationError(
                f"observation {observation_id} status must be one of "
                f"{sorted(_OBSERVATION_STATUSES)}"
            )
        evidence = observation.get("evidence")
        _require_text(f"observation {observation_id} evidence", evidence)
        if status == "present" and "value" not in observation:
            raise HandleSituationError(
                f"present observation {observation_id} requires value"
            )
        observations[observation_id] = deepcopy(dict(observation))
    return observations


def _charted_side(handle_view: Mapping[str, Any], expectation: Mapping[str, Any]) -> dict[str, Any]:
    raw = _require_mapping("expectation charted", expectation.get("charted"))
    status = raw.get("status")
    if status not in _CHARTED_STATUSES:
        raise HandleSituationError(
            f"charted status must be one of {sorted(_CHARTED_STATUSES)}"
        )

    result: dict[str, Any] = {"status": status}
    if status == "present":
        path = raw.get("path")
        if not isinstance(path, (list, tuple)) or not path:
            raise HandleSituationError("charted present requires a non-empty path")
        value = _at_path(handle_view, path)
        if value is _MISSING:
            raise HandleSituationError(
                "charted present path is missing; missing chart material is not absence"
            )
        result["path"] = deepcopy(list(path))
        result["value"] = deepcopy(value)
    else:
        # An explicit absence/unknown claim needs words naming the claim. This
        # prevents an omitted Handle field from being smuggled in as absence.
        claim = raw.get("claim")
        _require_text(f"charted {status} claim", claim)
        result["claim"] = claim
        if "path" in raw:
            path = raw["path"]
            if not isinstance(path, (list, tuple)) or not path:
                raise HandleSituationError("charted claim path must be non-empty")
            result["path"] = deepcopy(list(path))
    return result


def _compare_expectation(
    handle_view: Mapping[str, Any],
    expectation: Mapping[str, Any],
    observations: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    expectation_id = _require_text("expectation id", expectation.get("id"))
    observation_id = _require_text(
        f"expectation {expectation_id} observation", expectation.get("observation")
    )
    change_kind = expectation.get("compare_as", "value")
    if change_kind not in _CHANGE_KINDS:
        raise HandleSituationError(
            f"expectation {expectation_id} compare_as must be one of {sorted(_CHANGE_KINDS)}"
        )

    charted = _charted_side(handle_view, expectation)
    observation = observations.get(observation_id)

    if observation is None:
        return {
            "id": expectation_id,
            "charted": charted,
            "observation": observation_id,
            "runtime": {"status": "unobserved", "evidence": None},
            "result": "unobservable",
        }

    runtime_status = observation["status"]
    runtime = deepcopy(dict(observation))

    if runtime_status == "unobservable":
        result = "unobservable"
    elif charted["status"] == "unknown":
        result = f"charted-unknown/runtime-{runtime_status}"
    elif charted["status"] == "absent":
        result = (
            "charted-absent/runtime-present"
            if runtime_status == "present"
            else "confirmed-absent"
        )
    elif runtime_status == "absent":
        result = "charted-present/runtime-absent"
    elif charted["value"] == observation.get("value"):
        result = "confirmed"
    else:
        result = _CHANGE_KINDS[change_kind]

    return {
        "id": expectation_id,
        "charted": charted,
        "observation": observation_id,
        "runtime": runtime,
        "result": result,
    }


def _receipt_snapshot(receipt: CapabilityReceipt) -> dict[str, Any]:
    snapshot = asdict(receipt)
    snapshot["capacity"] = deepcopy(dict(receipt.capacity))
    return snapshot


def _match_snapshot(match: Any) -> dict[str, Any]:
    return {
        "requirement_id": match.requirement_id,
        "relation": match.relation,
        "detail": deepcopy(dict(match.detail)),
        "receipt": _receipt_snapshot(match.receipt),
        "handle": _receipt_snapshot(match.handle),
        "attenuated": match.attenuated,
    }


def resolve_handle_situation(
    handle_view: Mapping[str, Any],
    intent: Mapping[str, Any],
    environment_observations: Mapping[str, Any],
    capability_receipts: Iterable[CapabilityReceipt],
    requirements: Mapping[str, str | Demand] | None = None,
) -> dict[str, Any]:
    """Compare one HandleView with attributable Environment evidence.

    The result is an inspectable, copy-isolated Situation view. It may use the
    existing capability matcher to say which concrete receipts satisfy typed
    demands, but it performs no Closure or execution.
    """

    handle_view = _require_mapping("handle_view", handle_view)
    intent = _require_mapping("intent", intent)
    environment_observations = _require_mapping(
        "environment_observations", environment_observations
    )
    requirements = {} if requirements is None else _require_mapping("requirements", requirements)

    if handle_view.get("effectful") is not False:
        raise HandleSituationError("HandleView must be explicitly non-effectful")
    if handle_view.get("runtime_authority") not in ([], ()):
        raise HandleSituationError("HandleView cannot bring runtime authority into Situation")

    sources = _verify_handle_sources(handle_view)

    intent_id = _require_text("intent id", intent.get("id"))
    situation_input = _require_mapping("intent situation", intent.get("situation"))
    situation_id = _require_text("situation id", situation_input.get("id"))
    session_id = _require_text("session id", situation_input.get("session_id"))
    caster = _require_mapping("situation caster", situation_input.get("caster"))
    if "target" not in situation_input:
        raise HandleSituationError("intent situation requires target")

    environments_raw = situation_input.get("environments", ())
    if not isinstance(environments_raw, (list, tuple)) or not all(
        isinstance(item, str) and item for item in environments_raw
    ):
        raise HandleSituationError("situation environments must be strings")

    receipts = tuple(capability_receipts)
    if not all(isinstance(receipt, CapabilityReceipt) for receipt in receipts):
        raise HandleSituationError(
            "capability_receipts must already be concrete CapabilityReceipt values; "
            "Handle or observation prose is never promoted into a receipt"
        )

    observations = _normalize_observations(environment_observations)
    expectations = intent.get("expectations", [])
    if not isinstance(expectations, list):
        raise HandleSituationError("intent expectations must be a list")

    comparisons = tuple(
        _compare_expectation(handle_view, _require_mapping("expectation", item), observations)
        for item in expectations
    )
    drift = tuple(item for item in comparisons if item["result"] in _DRIFT_KINDS)
    uncertain = tuple(
        item
        for item in comparisons
        if item["result"] == "unobservable"
        or item["result"].startswith("charted-unknown/")
    )

    # Situation is constructed only from explicit situated inputs and concrete
    # Environment receipts. Handle claims never enter its capability tuple.
    situation = Situation(
        id=situation_id,
        session_id=session_id,
        caster=deepcopy(dict(caster)),
        target=deepcopy(situation_input["target"]),
        environments=tuple(environments_raw),
        capabilities=receipts,
        observations=deepcopy(observations),
    )
    plan = compile_cast_plan(requirements, situation)

    return {
        "situation_view_format": "0.1-work",
        "intent_id": intent_id,
        "handle_sources": deepcopy(dict(sources)),
        "handle_projection": deepcopy(handle_view.get("projection")),
        "situation": {
            "id": situation.id,
            "session_id": situation.session_id,
            "caster": deepcopy(situation.caster),
            "target": deepcopy(situation.target),
            "environments": list(situation.environments),
        },
        "environment": {
            "observations": deepcopy(observations),
            "capability_receipts": [_receipt_snapshot(receipt) for receipt in receipts],
        },
        "comparisons": list(comparisons),
        "drift": list(drift),
        "uncertain": list(uncertain),
        "capability_matching": {
            "matches": {
                requirement_id: _match_snapshot(match)
                for requirement_id, match in plan.matches.items()
            },
            "gaps": list(plan.gaps),
            "ready": plan.ready,
        },
        "affordances": ["inspect", "orient", "prepare-situation"],
        "runtime_authority": [],
        "effectful": False,
    }
