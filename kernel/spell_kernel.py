from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any, Callable

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
SPELL_SCHEMA = ROOT / "format" / "spell.schema.json"
FAMILIAR_SCHEMA = ROOT / "familiar" / "familiar.schema.json"
CAST_SCHEMA = ROOT / "kernel" / "cast.schema.json"


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _schema_validate(instance: dict[str, Any], schema_path: Path) -> None:
    schema = _load_json(schema_path)
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.validate(instance=instance, schema=schema)


def load_spell_md(path: str | Path) -> dict[str, Any]:
    text = Path(path).read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError("SPELL.md must begin with YAML frontmatter")
    end = text.find("\n---", 4)
    if end < 0:
        raise ValueError("SPELL.md frontmatter is not closed")
    data = yaml.safe_load(text[4:end])
    if not isinstance(data, dict):
        raise ValueError("SPELL.md frontmatter must be a mapping")
    validate_spell(data)
    return data


def validate_spell(spell: dict[str, Any]) -> None:
    _schema_validate(spell, SPELL_SCHEMA)
    telemetry_ids = [item["id"] for item in spell["telemetry"]]
    limit_ids = [item["id"] for item in spell["limits"]]
    effect_ids = [item["id"] for item in spell["effects"]]
    for label, ids in (("telemetry", telemetry_ids), ("limit", limit_ids), ("effect", effect_ids)):
        if len(ids) != len(set(ids)):
            raise ValueError(f"duplicate {label} id")
    telemetry_set = set(telemetry_ids)
    limit_set = set(limit_ids)
    for effect in spell["effects"]:
        unknown_telemetry = set(effect["telemetry"]) - telemetry_set
        unknown_limits = set(effect["limits"]) - limit_set
        if unknown_telemetry:
            raise ValueError(f"effect {effect['id']} references unknown telemetry: {sorted(unknown_telemetry)}")
        if unknown_limits:
            raise ValueError(f"effect {effect['id']} references unknown limits: {sorted(unknown_limits)}")
        req_ids = [item["id"] for item in effect["requirements"]]
        if len(req_ids) != len(set(req_ids)):
            raise ValueError(f"effect {effect['id']} has duplicate requirement id")


def validate_familiar(familiar: dict[str, Any]) -> None:
    _schema_validate(familiar, FAMILIAR_SCHEMA)


def validate_cast_record(record: dict[str, Any]) -> None:
    _schema_validate(record, CAST_SCHEMA)


Observer = Callable[[str, dict[str, Any]], dict[str, Any]]
Checker = Callable[[str, dict[str, Any]], bool]
AuthorityResolver = Callable[[dict[str, Any], str, dict[str, Any]], bool]
Executor = Callable[[dict[str, Any], str, dict[str, Any], int | None], Any]
Guide = Callable[[dict[str, Any], dict[str, Any], str, dict[str, Any]], Any]


class SpellKernel:
    def __init__(self, *, observers=None, requirements=None, limits=None, authority_resolver=None, executor=None, guide=None):
        self.observers = observers or {}
        self.requirements = requirements or {}
        self.limits = limits or {}
        self.authority_resolver = authority_resolver
        self.executor = executor
        self.guide = guide

    def _effect(self, spell: dict[str, Any], effect_id: str) -> dict[str, Any]:
        for effect in spell["effects"]:
            if effect["id"] == effect_id:
                return effect
        raise ValueError(f"unknown effect: {effect_id}")

    def _observe(self, telemetry: dict[str, Any], phase: str, context: dict[str, Any]) -> dict[str, Any]:
        telemetry_id = telemetry["id"]
        observer = self.observers.get(telemetry_id)
        if observer is None:
            return {"kind": "telemetry", "id": telemetry_id, "phase": phase, "status": "unavailable", "detail": "no observer registered"}
        try:
            result = observer(phase, context)
        except Exception as exc:
            return {"kind": "telemetry", "id": telemetry_id, "phase": phase, "status": "unavailable", "detail": f"observer failed: {type(exc).__name__}: {exc}"}
        observation = {"kind": "telemetry", "id": telemetry_id, "phase": phase, "status": "observed", "value": result.get("value"), "source": str(result.get("source", telemetry_id))}
        if "freshness_ms" in result:
            observation["freshness_ms"] = result["freshness_ms"]
        max_age = telemetry.get("max_age_ms")
        if max_age is not None:
            freshness = observation.get("freshness_ms")
            if freshness is None or freshness > max_age:
                observation["status"] = "unavailable"
                observation["detail"] = f"telemetry exceeds max_age_ms={max_age}"
        return observation

    @staticmethod
    def _check(kind: str, item_id: str, phase: str, checker, context: dict[str, Any]) -> dict[str, Any]:
        if checker is None:
            return {"kind": kind, "id": item_id, "phase": phase, "status": "unavailable", "detail": "no checker registered"}
        try:
            ok = bool(checker(phase, context))
        except Exception as exc:
            return {"kind": kind, "id": item_id, "phase": phase, "status": "unavailable", "detail": f"checker failed: {type(exc).__name__}: {exc}"}
        return {"kind": kind, "id": item_id, "phase": phase, "status": "satisfied" if ok else "violated"}

    def cast(
        self,
        spell: dict[str, Any],
        *,
        effect_id: str,
        caster: dict[str, Any],
        target: Any = None,
        familiar: dict[str, Any] | None = None,
        cast_id: str | None = None,
        execution_max_ms: int | None = None,
    ) -> dict[str, Any]:
        validate_spell(spell)
        if execution_max_ms is not None and (not isinstance(execution_max_ms, int) or execution_max_ms <= 0):
            raise ValueError("execution_max_ms must be a positive integer when provided")
        effect = self._effect(spell, effect_id)
        cast_id = cast_id or f"cast-{uuid.uuid4().hex[:12]}"
        context = {"spell": spell, "effect": effect, "caster": caster, "target": target}
        if execution_max_ms is not None:
            context["duration"] = {"execution_max_ms": execution_max_ms}
        observations = []
        reasons = []
        familiar_ref = None
        guidance = None
        if familiar is not None:
            try:
                validate_familiar(familiar)
            except Exception as exc:
                reasons.append(f"familiar-invalid: {exc}")
            else:
                familiar_ref = {"id": familiar["id"]}
                context["familiar"] = familiar
                guidance = self.guide(familiar, spell, effect_id, context) if self.guide is not None else {"dialect": familiar["dialect"], "attention": familiar["attention"], "preferences": familiar["preferences"]}
        telemetry_by_id = {item["id"]: item for item in spell["telemetry"]}
        for telemetry_id in effect["telemetry"]:
            observation = self._observe(telemetry_by_id[telemetry_id], "before", context)
            observations.append(observation)
            context.setdefault("telemetry", {})[telemetry_id] = observation
            if observation["status"] != "observed":
                reasons.append(f"telemetry-unavailable: {telemetry_id}")
        for authority in effect["authority"]:
            allowed = False
            if self.authority_resolver is not None:
                try:
                    allowed = bool(self.authority_resolver(caster, authority, context))
                except Exception:
                    allowed = False
            observations.append({"kind": "authority", "id": authority, "phase": "before", "status": "satisfied" if allowed else "denied"})
            if not allowed:
                reasons.append(f"authority-denied: {authority}")
        for requirement in effect["requirements"]:
            if requirement["phase"] != "before":
                continue
            obs = self._check("requirement", requirement["id"], "before", self.requirements.get(requirement["id"]), context)
            observations.append(obs)
            if obs["status"] != "satisfied":
                reasons.append(f"requirement-unsatisfied: {requirement['id']}")
        for limit_id in effect["limits"]:
            obs = self._check("limit", limit_id, "before", self.limits.get(limit_id), context)
            observations.append(obs)
            if obs["status"] != "satisfied":
                reasons.append(f"limit-unresolved: {limit_id}")
        record = {"cast_format": "0.2", "cast_id": cast_id, "spell": {"name": spell["name"], "version": spell["version"]}, "caster": {"id": caster["id"], "kind": caster["kind"]}, "familiar": familiar_ref, "guidance": guidance, "effect": effect_id, "closure": {"decision": "refused" if reasons else "closed", "reasons": reasons}, "observations": observations, "outcome": None, "residuals": []}
        if reasons:
            validate_cast_record(record)
            return record
        execution_failed = False
        started = time.monotonic()
        try:
            if self.executor is None:
                raise RuntimeError("no executor registered")
            record["result"] = self.executor(spell, effect_id, context, execution_max_ms)
            elapsed_ms = round((time.monotonic() - started) * 1000, 3)
            if execution_max_ms is not None:
                execution_value = {"elapsed_ms": elapsed_ms, "max_ms": execution_max_ms}
                if elapsed_ms > execution_max_ms:
                    execution_failed = True
                    observations.append({"kind": "execution", "id": effect_id, "phase": "after", "status": "failed", "value": execution_value, "detail": "execution exceeded duration bound"})
                    record["residuals"].append(f"execution exceeded duration: {elapsed_ms}ms > {execution_max_ms}ms")
                else:
                    observations.append({"kind": "execution", "id": effect_id, "phase": "after", "status": "satisfied", "value": execution_value})
            else:
                observations.append({"kind": "execution", "id": effect_id, "phase": "after", "status": "satisfied"})
        except Exception as exc:
            elapsed_ms = round((time.monotonic() - started) * 1000, 3)
            execution_failed = True
            record["result"] = None
            observation = {"kind": "execution", "id": effect_id, "phase": "after", "status": "failed", "detail": f"{type(exc).__name__}: {exc}"}
            if execution_max_ms is not None:
                observation["value"] = {"elapsed_ms": elapsed_ms, "max_ms": execution_max_ms}
            observations.append(observation)
            record["residuals"].append(f"execution failed: {type(exc).__name__}: {exc}")
        for telemetry_id in effect["telemetry"]:
            observation = self._observe(telemetry_by_id[telemetry_id], "after", context)
            observations.append(observation)
            context.setdefault("telemetry_after", {})[telemetry_id] = observation
        post_failed = False
        for requirement in [r for r in effect["requirements"] if r["phase"] == "after"]:
            obs = self._check("requirement", requirement["id"], "after", self.requirements.get(requirement["id"]), context)
            observations.append(obs)
            if obs["status"] != "satisfied":
                post_failed = True
                record["residuals"].append(f"effect requirement unresolved: {requirement['id']}")
        limit_failed = False
        for limit_id in effect["limits"]:
            obs = self._check("limit", limit_id, "after", self.limits.get(limit_id), context)
            observations.append(obs)
            if obs["status"] != "satisfied":
                limit_failed = True
                record["residuals"].append(f"limit violated after execution: {limit_id}")
        if execution_failed or limit_failed:
            record["outcome"] = "failed"
        elif post_failed:
            record["outcome"] = "partial"
        else:
            record["outcome"] = "resolved"
        validate_cast_record(record)
        return record
