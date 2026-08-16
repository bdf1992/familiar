from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any, Callable

import jsonschema
import yaml

from kernel.resources import CAST_SCHEMA, FAMILIAR_SCHEMA, SPELL_SCHEMA

ROOT = Path(__file__).resolve().parents[1]


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
ScopeResolver = Callable[[Any, dict[str, Any]], list[Any]]


class SpellKernel:
    def __init__(
        self,
        *,
        observers=None,
        requirements=None,
        limits=None,
        authority_resolver=None,
        executor=None,
        guide=None,
        scope_resolver=None,
        scope_enforcer=None,
        authority_enforcer=None,
        consequence_classifier=None,
        compensation_provider=None,
        executor_id=None,
    ):
        self.observers = observers or {}
        self.requirements = requirements or {}
        self.limits = limits or {}
        self.authority_resolver = authority_resolver
        self.executor = executor
        self.guide = guide
        self.scope_resolver = scope_resolver
        # Environment-owned effect-path boundary. The Kernel calls it and never
        # constructs one: a runtime that supplies its own containment is
        # attesting to its own honesty.
        self.scope_enforcer = scope_enforcer
        # The same split at the Authority boundary. Resolution says the caster
        # may attempt; only attenuation constrains what the executor can reach.
        self.authority_enforcer = authority_enforcer
        # Environment-owned classification of what the world kept. The Kernel
        # can observe a local mutation; only the Environment can say whether an
        # external consequence was undone, persists, or can be compensated.
        self.consequence_classifier = consequence_classifier
        self.compensation_provider = compensation_provider
        # Identity of the effect path, used to refuse a rollback claim the
        # executor makes about itself.
        self.executor_id = executor_id

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
        cost_max: dict[str, int] | None = None,
        scope_max_items: int | None = None,
        compensation_required: bool = False,
    ) -> dict[str, Any]:
        validate_spell(spell)
        if execution_max_ms is not None and (not isinstance(execution_max_ms, int) or execution_max_ms <= 0):
            raise ValueError("execution_max_ms must be a positive integer when provided")
        if cost_max is not None:
            if not isinstance(cost_max, dict):
                raise ValueError("cost_max must be a mapping when provided")
            for resource, ceiling in cost_max.items():
                if not isinstance(resource, str) or not resource:
                    raise ValueError("cost_max resource names must be non-empty strings")
                if not isinstance(ceiling, int) or ceiling < 0:
                    raise ValueError("cost_max ceilings must be non-negative integers")
        if scope_max_items is not None and (not isinstance(scope_max_items, int) or scope_max_items < 0):
            raise ValueError("scope_max_items must be a non-negative integer when provided")
        effect = self._effect(spell, effect_id)
        cast_id = cast_id or f"cast-{uuid.uuid4().hex[:12]}"
        context = {"spell": spell, "effect": effect, "caster": caster, "target": target}
        if execution_max_ms is not None:
            context["duration"] = {"execution_max_ms": execution_max_ms}
        cost_used: dict[str, int] = {}
        if cost_max is not None:
            def charge(resource: str, amount: int = 1) -> int:
                if resource not in cost_max:
                    raise RuntimeError(f"cost resource not permitted: {resource}")
                if not isinstance(amount, int) or amount <= 0:
                    raise RuntimeError("cost amount must be a positive integer")
                next_value = cost_used.get(resource, 0) + amount
                if next_value > cost_max[resource]:
                    raise RuntimeError(f"cost exceeded: {resource} {next_value}>{cost_max[resource]}")
                cost_used[resource] = next_value
                return next_value
            context["cost"] = {"max": dict(cost_max), "used": cost_used, "charge": charge}
        observations = []
        reasons = []
        scope_boundary = None
        authority_boundary = None
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
        if scope_max_items is not None:
            if self.scope_resolver is None:
                observations.append({"kind": "requirement", "id": "scope-max-items", "phase": "before", "status": "unavailable", "detail": "no scope resolver registered"})
                reasons.append("requirement-unsatisfied: scope-max-items")
            else:
                try:
                    resolved_items = list(self.scope_resolver(target, context))
                except Exception as exc:
                    observations.append({"kind": "requirement", "id": "scope-max-items", "phase": "before", "status": "unavailable", "detail": f"scope resolution failed: {type(exc).__name__}: {exc}"})
                    reasons.append("requirement-unsatisfied: scope-max-items")
                else:
                    count = len(resolved_items)
                    context["scope"] = {"target": target, "items": resolved_items, "max_items": scope_max_items}
                    status = "satisfied" if count <= scope_max_items else "violated"
                    value = {
                        "target": target,
                        "items": resolved_items,
                        "count": count,
                        "max_items": scope_max_items,
                    }
                    # Resolution is not enforcement. A resolved Scope binds the
                    # effect path only through a concrete Environment boundary,
                    # so closure refuses when none can be supplied rather than
                    # trusting the Technique to honour a preflight result.
                    if status == "satisfied":
                        if self.scope_enforcer is None:
                            status = "unavailable"
                            value["detail"] = "no scope enforcer registered; effect path is unbounded"
                        else:
                            try:
                                scope_boundary = self.scope_enforcer(target, resolved_items, context)
                                handle = scope_boundary.handle()
                            except Exception as exc:
                                scope_boundary = None
                                status = "unavailable"
                                value["detail"] = f"scope enforcement failed: {type(exc).__name__}: {exc}"
                            else:
                                context["target"] = handle
                                context["scope"]["handle"] = handle
                                value["enforcement"] = scope_boundary.describe()
                    observations.append({
                        "kind": "requirement",
                        "id": "scope-max-items",
                        "phase": "before",
                        "status": status,
                        "value": value,
                    })
                    if status != "satisfied":
                        reasons.append("requirement-unsatisfied: scope-max-items")
        granted_authorities = []
        for authority in effect["authority"]:
            allowed = False
            if self.authority_resolver is not None:
                try:
                    allowed = bool(self.authority_resolver(caster, authority, context))
                except Exception:
                    allowed = False
            observations.append({"kind": "authority", "id": authority, "phase": "before", "status": "satisfied" if allowed else "denied"})
            if allowed:
                granted_authorities.append(authority)
            else:
                reasons.append(f"authority-denied: {authority}")
        # Resolution is not enforcement. A resolved Authority binds the effect
        # path only through a credential no broader than the one that closed the
        # Cast, so closure refuses when none can be supplied rather than letting
        # the executor keep whatever the host ambiently holds.
        if effect["authority"] and len(granted_authorities) == len(effect["authority"]):
            enforcement = {
                "kind": "authority",
                "id": "authority-enforcement",
                "phase": "before",
                "status": "satisfied",
                "value": {"resolved": list(granted_authorities)},
            }
            if self.authority_enforcer is None:
                enforcement["status"] = "unavailable"
                enforcement["detail"] = "no authority enforcer registered; execution credential is ambient"
                reasons.append("authority-unenforced: no attenuated execution capability")
            else:
                try:
                    authority_boundary = self.authority_enforcer(caster, list(granted_authorities), context)
                    credential = authority_boundary.handle()
                except Exception as exc:
                    authority_boundary = None
                    enforcement["status"] = "unavailable"
                    enforcement["detail"] = f"authority attenuation failed: {type(exc).__name__}: {exc}"
                    reasons.append("authority-unenforced: attenuation failed")
                else:
                    context["authority"] = credential
                    enforcement["value"]["enforcement"] = authority_boundary.describe()
            observations.append(enforcement)
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
        # Where compensation is required, refuse before the effect rather than
        # discovering afterwards that the world kept something with no path back.
        if compensation_required and self.compensation_provider is None:
            observations.append({
                "kind": "execution",
                "id": "compensation-support",
                "phase": "before",
                "status": "unavailable",
                "detail": "compensation required but no compensation provider is registered",
            })
            reasons.append("compensation-unsupported: no compensation path available")
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
            execution_value: dict[str, Any] = {}
            if execution_max_ms is not None:
                execution_value["duration"] = {"elapsed_ms": elapsed_ms, "max_ms": execution_max_ms}
            if cost_max is not None:
                execution_value["cost"] = {"used": dict(cost_used), "max": dict(cost_max)}
            if execution_max_ms is not None and elapsed_ms > execution_max_ms:
                execution_failed = True
                observation = {"kind": "execution", "id": effect_id, "phase": "after", "status": "failed", "detail": "execution exceeded duration bound"}
                if execution_value:
                    observation["value"] = execution_value
                observations.append(observation)
                record["residuals"].append(f"execution exceeded duration: {elapsed_ms}ms > {execution_max_ms}ms")
            else:
                observation = {"kind": "execution", "id": effect_id, "phase": "after", "status": "satisfied"}
                if execution_value:
                    observation["value"] = execution_value
                observations.append(observation)
        except Exception as exc:
            elapsed_ms = round((time.monotonic() - started) * 1000, 3)
            execution_failed = True
            record["result"] = None
            observation = {"kind": "execution", "id": effect_id, "phase": "after", "status": "failed", "detail": f"{type(exc).__name__}: {exc}"}
            execution_value = {}
            if execution_max_ms is not None:
                execution_value["duration"] = {"elapsed_ms": elapsed_ms, "max_ms": execution_max_ms}
            if cost_max is not None:
                execution_value["cost"] = {"used": dict(cost_used), "max": dict(cost_max)}
            if execution_value:
                observation["value"] = execution_value
            observations.append(observation)
            record["residuals"].append(f"execution failed: {type(exc).__name__}: {exc}")
        for telemetry_id in effect["telemetry"]:
            observation = self._observe(telemetry_by_id[telemetry_id], "after", context)
            observations.append(observation)
            context.setdefault("telemetry_after", {})[telemetry_id] = observation
        # Read the boundary rather than the Technique's account of itself. An
        # attempt the Technique caught and swallowed is still attributable, so
        # containment is proven by the mechanism and not by an absent exception.
        scope_failed = False
        if scope_boundary is not None:
            breaches = scope_boundary.violations()
            observations.append({
                "kind": "requirement",
                "id": "scope-max-items",
                "phase": "after",
                "status": "violated" if breaches else "satisfied",
                "value": {
                    "enforcement": scope_boundary.describe(),
                    "violations": [item.as_dict() for item in breaches],
                },
            })
            if breaches:
                scope_failed = True
                record["residuals"].append(
                    f"scope violated during execution: {len(breaches)} attempt(s) outside resolved Scope"
                )
        # Classify what the world kept. Three outcomes a failed postcondition
        # would otherwise collapse: nothing happened, it was undone, it persists.
        if self.consequence_classifier is not None:
            try:
                finding = self.consequence_classifier(spell, effect_id, context, execution_failed)
                # An inverse-looking API is not evidence that state was
                # restored. The Kernel reads the finding structurally and
                # imports nothing from the Environment to do it.
                if (
                    self.executor_id is not None
                    and finding.kind == "reversed"
                    and finding.observer == self.executor_id
                ):
                    raise ValueError(
                        f"exact reversal requires an observer independent of the executor; "
                        f"{self.executor_id!r} cannot certify its own rollback"
                    )
            except Exception as exc:
                observations.append({
                    "kind": "execution",
                    "id": "consequence",
                    "phase": "after",
                    "status": "unavailable",
                    "detail": f"consequence classification failed: {type(exc).__name__}: {exc}",
                })
                record["residuals"].append(
                    f"consequence unclassified: {type(exc).__name__}: {exc}"
                )
            else:
                observations.append({
                    "kind": "execution",
                    "id": "consequence",
                    "phase": "after",
                    "status": "violated" if finding.persistent else "satisfied",
                    "value": finding.as_dict(),
                })
                if finding.persistent:
                    detail = (
                        f"compensatable via {finding.compensation}"
                        if finding.kind == "compensatable"
                        else "no compensation path declared"
                    )
                    record["residuals"].append(
                        f"persistent world mutation ({finding.kind}): {detail}"
                    )
        authority_failed = False
        if authority_boundary is not None:
            breaches = authority_boundary.violations()
            observations.append({
                "kind": "authority",
                "id": "authority-enforcement",
                "phase": "after",
                "status": "violated" if breaches else "satisfied",
                "value": {
                    "enforcement": authority_boundary.describe(),
                    "violations": [item.as_dict() for item in breaches],
                },
            })
            if breaches:
                authority_failed = True
                record["residuals"].append(
                    f"authority violated during execution: {len(breaches)} attempt(s) beyond resolved authority"
                )
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
        if execution_failed or limit_failed or scope_failed or authority_failed:
            record["outcome"] = "failed"
        elif post_failed:
            record["outcome"] = "partial"
        else:
            record["outcome"] = "resolved"
        validate_cast_record(record)
        return record
