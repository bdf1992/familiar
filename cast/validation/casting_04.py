from __future__ import annotations

import json
import uuid
from copy import deepcopy
from pathlib import Path
from typing import Any

import jsonschema

from kernel.spell_kernel import SpellKernel
from validation.candidate_adapter import cast_candidate, validate_candidate_spell

ROOT = Path(__file__).resolve().parents[1]
BINDING_SCHEMA = ROOT / "kernel" / "0.4-draft" / "technique-binding.schema.json"
CAST_SCHEMA = ROOT / "kernel" / "0.4-draft" / "cast.schema.json"


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _validate(instance: dict[str, Any], schema_path: Path) -> None:
    schema = _load_json(schema_path)
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.validate(instance=instance, schema=schema)


def validate_technique_binding(binding: dict[str, Any]) -> None:
    _validate(binding, BINDING_SCHEMA)


def validate_cast_04(record: dict[str, Any]) -> None:
    _validate(record, CAST_SCHEMA)


def _effect(spell: dict[str, Any], effect_id: str) -> dict[str, Any]:
    for effect in spell["effects"]:
        if effect["id"] == effect_id:
            return effect
    raise ValueError(f"unknown effect: {effect_id}")


def binding_support_gaps(
    kernel: SpellKernel,
    spell: dict[str, Any],
    effect_id: str,
    binding: dict[str, Any],
) -> list[str]:
    """Return closure blockers before any effectful execution is attempted."""
    validate_candidate_spell(spell)
    validate_technique_binding(binding)
    effect = _effect(spell, effect_id)
    realizes = binding["realizes"]
    gaps: list[str] = []

    if realizes["spell"] != spell["name"]:
        gaps.append(f"binding-spell-mismatch: {realizes['spell']} != {spell['name']}")
    if realizes["spell_version"] != spell["version"]:
        gaps.append(f"binding-version-mismatch: {realizes['spell_version']} != {spell['version']}")
    if realizes["effect"] != effect_id:
        gaps.append(f"binding-effect-mismatch: {realizes['effect']} != {effect_id}")

    mechanisms = binding["mechanisms"]
    requirements = effect["requirements"]

    for telemetry_id in effect["telemetry"]:
        if telemetry_id not in kernel.observers:
            gaps.append(f"runtime-observer-missing: {telemetry_id}")

    for item in requirements["before"]:
        requirement_id = item["id"]
        if "authority" in item:
            if kernel.authority_resolver is None:
                gaps.append(f"runtime-authority-resolver-missing: {requirement_id}")
            if not mechanisms["authority"]:
                gaps.append(f"binding-authority-boundary-missing: {requirement_id}")
        elif "scope" in item:
            if kernel.scope_resolver is None:
                gaps.append(f"runtime-scope-resolver-missing: {requirement_id}")
            # A binding that claims Scope support without an enforceable effect
            # path is claiming metadata. Refuse before execution, not after.
            if kernel.scope_enforcer is None:
                gaps.append(f"runtime-scope-enforcer-missing: {requirement_id}")
            if "max_items" not in mechanisms["scope"]:
                gaps.append(f"binding-scope-boundary-missing: {requirement_id}")
        elif requirement_id not in kernel.requirements:
            gaps.append(f"runtime-checker-missing: {requirement_id}")

    for item in requirements["during"]:
        requirement_id = item["id"]
        if "cost" in item:
            resource = item["cost"]["resource"]
            if resource not in mechanisms["cost"]:
                gaps.append(f"binding-cost-meter-missing: {requirement_id}:{resource}")
        elif "duration" in item:
            if "execution_max_ms" not in mechanisms["duration"]:
                gaps.append(f"binding-duration-containment-missing: {requirement_id}")

    for item in requirements["after"]:
        requirement_id = item["id"]
        if requirement_id not in kernel.requirements:
            gaps.append(f"runtime-checker-missing: {requirement_id}")

    return gaps


def _refused_record(
    spell: dict[str, Any],
    effect_id: str,
    caster: dict[str, Any],
    target: Any,
    binding: dict[str, Any],
    familiar: dict[str, Any] | None,
    cast_id: str | None,
    reasons: list[str],
) -> dict[str, Any]:
    record = {
        "cast_format": "0.4-draft",
        "cast_id": cast_id or f"cast-{uuid.uuid4().hex[:12]}",
        "spell": {"name": spell["name"], "version": spell["version"]},
        "caster": {"id": caster["id"], "kind": caster["kind"]},
        "target": deepcopy(target),
        "technique": {"id": binding["id"], "version": binding["version"], "kind": binding["kind"]},
        "familiar": {"id": familiar["id"]} if familiar is not None and "id" in familiar else None,
        "guidance": None,
        "effect": effect_id,
        "closure": {"decision": "refused", "reasons": reasons},
        "observations": [],
        "outcome": None,
        "residuals": [],
    }
    validate_cast_04(record)
    return record


def cast_with_binding(
    kernel: SpellKernel,
    spell: dict[str, Any],
    binding: dict[str, Any],
    *,
    effect_id: str,
    caster: dict[str, Any],
    target: Any,
    familiar: dict[str, Any] | None = None,
    cast_id: str | None = None,
    downstream_containment_required: bool = False,
) -> dict[str, Any]:
    """Run the 0.3 candidate through the 0.4 binding/closure check."""
    gaps = binding_support_gaps(kernel, spell, effect_id, binding)
    if gaps:
        return _refused_record(spell, effect_id, caster, target, binding, familiar, cast_id, gaps)

    record = cast_candidate(
        kernel,
        spell,
        effect_id=effect_id,
        caster=caster,
        target=target,
        familiar=familiar,
        cast_id=cast_id,
        downstream_containment_required=downstream_containment_required,
    )
    record["cast_format"] = "0.4-draft"
    record["technique"] = {"id": binding["id"], "version": binding["version"], "kind": binding["kind"]}
    validate_cast_04(record)
    return record
