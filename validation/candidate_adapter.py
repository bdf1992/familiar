from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from kernel.spell_kernel import SpellKernel

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ROOT = Path(__file__).resolve().parent / "candidate"
SPELL_SCHEMA = CANDIDATE_ROOT / "spell.schema.json"
CAST_SCHEMA = CANDIDATE_ROOT / "cast.schema.json"


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _schema_validate(instance: dict[str, Any], schema_path: Path) -> None:
    schema = _load_json(schema_path)
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.validate(instance=instance, schema=schema)


def load_candidate_spell(path: str | Path) -> dict[str, Any]:
    text = Path(path).read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError("candidate SPELL.md must begin with YAML frontmatter")
    end = text.find("\n---", 4)
    if end < 0:
        raise ValueError("candidate SPELL.md frontmatter is not closed")
    data = yaml.safe_load(text[4:end])
    if not isinstance(data, dict):
        raise ValueError("candidate SPELL.md frontmatter must be a mapping")
    validate_candidate_spell(data)
    return data


def validate_candidate_spell(spell: dict[str, Any]) -> None:
    _schema_validate(spell, SPELL_SCHEMA)
    telemetry_ids = [item["id"] for item in spell["telemetry"]]
    if len(telemetry_ids) != len(set(telemetry_ids)):
        raise ValueError("duplicate telemetry id")
    telemetry_set = set(telemetry_ids)
    effect_ids = [effect["id"] for effect in spell["effects"]]
    if len(effect_ids) != len(set(effect_ids)):
        raise ValueError("duplicate effect id")

    for effect in spell["effects"]:
        unknown = set(effect["telemetry"]) - telemetry_set
        if unknown:
            raise ValueError(f"effect {effect['id']} references unknown telemetry: {sorted(unknown)}")
        requirements = effect["requirements"]
        all_requirements = requirements["before"] + requirements["during"] + requirements["after"]
        ids = [item["id"] for item in all_requirements]
        if len(ids) != len(set(ids)):
            raise ValueError(f"effect {effect['id']} has duplicate requirement id")
        scopes = [item for item in requirements["before"] if "scope" in item]
        if len(scopes) > 1:
            raise ValueError(f"effect {effect['id']} has more than one scope requirement")
        durations = [item for item in requirements["during"] if "duration" in item]
        if len(durations) > 1:
            raise ValueError(f"effect {effect['id']} has more than one duration requirement")
        cost_resources = [item["cost"]["resource"] for item in requirements["during"] if "cost" in item]
        if len(cost_resources) != len(set(cost_resources)):
            raise ValueError(f"effect {effect['id']} has duplicate cost resource")


def validate_candidate_cast(record: dict[str, Any]) -> None:
    _schema_validate(record, CAST_SCHEMA)


def _effect(spell: dict[str, Any], effect_id: str) -> dict[str, Any]:
    for effect in spell["effects"]:
        if effect["id"] == effect_id:
            return effect
    raise ValueError(f"unknown effect: {effect_id}")


def _ordinary(item: dict[str, Any], phase: str) -> dict[str, Any]:
    return {"id": item["id"], "phase": phase, "description": item["description"]}


def _runtime_plan(spell: dict[str, Any], effect: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    requirements = effect["requirements"]
    ordinary_before = [item for item in requirements["before"] if set(item).issubset({"id", "description"})]
    ordinary_after = list(requirements["after"])
    authority_requirements = [item for item in requirements["before"] if "authority" in item]
    scope_requirements = [item for item in requirements["before"] if "scope" in item]
    cost_requirements = [item for item in requirements["during"] if "cost" in item]
    duration_requirements = [item for item in requirements["during"] if "duration" in item]

    normalized = {
        "spell_format": "0.2",
        "name": spell["name"],
        "version": spell["version"],
        "description": spell["description"],
        "telemetry": deepcopy(spell["telemetry"]),
        "limits": [],
        "effects": [
            {
                "id": effect["id"],
                "description": effect["description"],
                "telemetry": list(effect["telemetry"]),
                "requirements": [
                    *[_ordinary(item, "before") for item in ordinary_before],
                    *[_ordinary(item, "after") for item in ordinary_after],
                ],
                "limits": [],
                "authority": [item["authority"] for item in authority_requirements],
            }
        ],
    }

    plan: dict[str, Any] = {
        "authority": authority_requirements,
        "scope": scope_requirements[0] if scope_requirements else None,
        "cost": cost_requirements,
        "duration": duration_requirements[0] if duration_requirements else None,
    }
    return normalized, plan


def _candidate_record(
    record: dict[str, Any],
    *,
    target: Any,
    plan: dict[str, Any],
) -> dict[str, Any]:
    result = deepcopy(record)
    result["cast_format"] = "0.3-candidate"
    result["target"] = deepcopy(target)

    authority_by_permission = {item["authority"]: item for item in plan["authority"]}
    for observation in result["observations"]:
        if observation["kind"] == "authority" and observation["id"] in authority_by_permission:
            declaration = authority_by_permission[observation["id"]]
            permission = observation["id"]
            observation["kind"] = "requirement"
            observation["id"] = declaration["id"]
            observation["value"] = {"authority": permission}
        if observation["kind"] == "requirement" and observation["id"] == "scope-max-items" and plan["scope"]:
            observation["id"] = plan["scope"]["id"]

    execution = next((item for item in result["observations"] if item["kind"] == "execution"), None)
    execution_value = (execution or {}).get("value") or {}
    execution_detail = (execution or {}).get("detail", "")

    for cost_requirement in plan["cost"]:
        cost = cost_requirement["cost"]
        cost_value = (execution_value.get("cost") or {})
        used = (cost_value.get("used") or {}).get(cost["resource"])
        maximum = (cost_value.get("max") or {}).get(cost["resource"])
        if used is None and maximum is None:
            continue
        violated = "cost exceeded" in execution_detail or any("cost exceeded" in residual for residual in result["residuals"])
        result["observations"].append(
            {
                "kind": "requirement",
                "id": cost_requirement["id"],
                "phase": "during",
                "status": "violated" if violated else "satisfied",
                "value": {"resource": cost["resource"], "used": used, "max": maximum},
            }
        )

    duration_requirement = plan["duration"]
    if duration_requirement:
        duration_value = execution_value.get("duration")
        if duration_value:
            elapsed = duration_value.get("elapsed_ms")
            maximum = duration_value.get("max_ms")
            violated = isinstance(elapsed, (int, float)) and isinstance(maximum, (int, float)) and elapsed > maximum
            if "TimeoutExpired" in execution_detail or "duration bound" in execution_detail:
                violated = True
            result["observations"].append(
                {
                    "kind": "requirement",
                    "id": duration_requirement["id"],
                    "phase": "during",
                    "status": "violated" if violated else "satisfied",
                    "value": duration_value,
                }
            )

    validate_candidate_cast(result)
    return result


def cast_candidate(
    kernel: SpellKernel,
    spell: dict[str, Any],
    *,
    effect_id: str,
    caster: dict[str, Any],
    target: Any,
    familiar: dict[str, Any] | None = None,
    cast_id: str | None = None,
) -> dict[str, Any]:
    validate_candidate_spell(spell)
    effect = _effect(spell, effect_id)
    normalized, plan = _runtime_plan(spell, effect)

    scope_max_items = plan["scope"]["scope"]["max_items"] if plan["scope"] else None
    cost_max = {item["cost"]["resource"]: item["cost"]["max"] for item in plan["cost"]} or None
    execution_max_ms = plan["duration"]["duration"]["execution_max_ms"] if plan["duration"] else None

    record = kernel.cast(
        normalized,
        effect_id=effect_id,
        caster=caster,
        target=target,
        familiar=familiar,
        cast_id=cast_id,
        execution_max_ms=execution_max_ms,
        cost_max=cost_max,
        scope_max_items=scope_max_items,
    )
    return _candidate_record(record, target=target, plan=plan)
