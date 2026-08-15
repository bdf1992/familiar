"""Reference Spell runtime baseline.

This module intentionally avoids transport concerns. It validates portable Spell
claims, checks whether a concrete cast may proceed, and derives only the
standing that current evidence can justify.

Higher Spell levels are deliberately not guessed from a point score. v0 can
prove Trick standing or Level 0; Levels 1-9 require future published trial
rubrics and independent examples.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


PROTOCOL_VERSION = "0.1"
LEVEL_ZERO_PROOFS = {
    "effect",
    "telemetry-sensitive",
    "requirements",
    "limits",
    "evidence",
}


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str


@dataclass(frozen=True)
class Standing:
    kind: str  # "trick" | "spell"
    trick: str | None = None
    demonstrated_level: int | None = None
    grade: str = "provisional"
    missing_proofs: tuple[str, ...] = ()


def _ids(items: Iterable[dict[str, Any]]) -> list[str]:
    return [str(item.get("id", "")) for item in items]


def _duplicates(values: Iterable[str]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return duplicates


def validate_definition(spell: dict[str, Any]) -> list[ValidationIssue]:
    """Validate semantic invariants that JSON Schema alone cannot protect."""

    issues: list[ValidationIssue] = []

    if spell.get("spell_protocol") != PROTOCOL_VERSION:
        issues.append(
            ValidationIssue(
                "protocol-version",
                f"spell_protocol must be {PROTOCOL_VERSION!r}",
            )
        )

    identity = spell.get("identity") or {}
    for field in ("id", "name", "version", "inherent_ability"):
        if not identity.get(field):
            issues.append(ValidationIssue("identity", f"identity.{field} is required"))

    expressions = (spell.get("invocation") or {}).get("expressions") or []
    if not expressions:
        issues.append(ValidationIssue("expression", "at least one expression is required"))
    for duplicate in sorted(_duplicates(_ids(expressions))):
        issues.append(ValidationIssue("duplicate-expression", f"duplicate expression id: {duplicate}"))

    telemetry = spell.get("telemetry") or {}
    required_telemetry = telemetry.get("required") or []
    optional_telemetry = telemetry.get("optional") or []
    for duplicate in sorted(_duplicates(_ids(required_telemetry + optional_telemetry))):
        issues.append(ValidationIssue("duplicate-telemetry", f"duplicate telemetry id: {duplicate}"))

    for key in ("requirements", "limits"):
        items = spell.get(key) or []
        for duplicate in sorted(_duplicates(_ids(items))):
            issues.append(ValidationIssue(f"duplicate-{key}", f"duplicate {key} id: {duplicate}"))

    evidence_required = ((spell.get("evidence") or {}).get("required") or [])
    if not evidence_required:
        issues.append(
            ValidationIssue(
                "evidence",
                "a Spell candidate must declare at least one effect evidence requirement",
            )
        )

    claimed_level = (spell.get("evaluation") or {}).get("claimed_level")
    if claimed_level is not None and (not isinstance(claimed_level, int) or not 0 <= claimed_level <= 9):
        issues.append(ValidationIssue("claimed-level", "claimed_level must be an integer from 0 through 9"))

    return issues


def evaluate_trials(results: Iterable[dict[str, Any]]) -> Standing:
    """Derive demonstrated standing from passed Trial proof tags.

    v0 intentionally caps automatic Spell classification at Level 0. This
    avoids converting an arbitrary point total into fictional high-level
    Spellcraft before Levels 1-9 have independent conformance suites.
    """

    passed = [result for result in results if result.get("passed") is True]
    proofs: set[str] = set()
    for result in passed:
        proofs.update(str(proof) for proof in (result.get("proves") or []))

    missing = tuple(sorted(LEVEL_ZERO_PROOFS - proofs))
    if not missing:
        return Standing(kind="spell", demonstrated_level=0, missing_proofs=())

    # Trick rank measures demonstrated bounded craft, not shame or failure.
    if "effect" not in proofs:
        trick = "novice"
    elif len(proofs & LEVEL_ZERO_PROOFS) >= 3:
        trick = "master"
    else:
        trick = "practiced"

    return Standing(kind="trick", trick=trick, missing_proofs=missing)


def validate_cast(spell: dict[str, Any], cast: dict[str, Any]) -> list[ValidationIssue]:
    """Check whether runtime state supports the cast status it claims."""

    issues = list(validate_definition(spell))
    if issues:
        return issues

    identity = spell["identity"]
    cast_spell = cast.get("spell") or {}
    if cast_spell.get("id") != identity["id"] or cast_spell.get("version") != identity["version"]:
        issues.append(ValidationIssue("spell-identity", "cast spell id/version does not match definition"))

    known_expressions = {item["id"] for item in spell["invocation"]["expressions"]}
    if cast.get("expression") not in known_expressions:
        issues.append(ValidationIssue("expression", f"unknown expression: {cast.get('expression')!r}"))

    observations = {item.get("id"): item for item in (cast.get("telemetry") or [])}
    for requirement in spell["telemetry"]["required"]:
        observation = observations.get(requirement["id"])
        if observation is None:
            issues.append(ValidationIssue("telemetry-missing", f"missing telemetry: {requirement['id']}"))
            continue
        max_age = requirement.get("max_age_ms")
        freshness = observation.get("freshness_ms")
        if max_age is not None and (freshness is None or freshness > max_age):
            issues.append(
                ValidationIssue(
                    "telemetry-stale",
                    f"telemetry {requirement['id']} exceeds max_age_ms={max_age}",
                )
            )

    requirement_checks = {item.get("id"): item for item in (cast.get("requirements") or [])}
    for requirement in spell.get("requirements") or []:
        check = requirement_checks.get(requirement["id"])
        if check is None or check.get("status") != "satisfied":
            issues.append(ValidationIssue("requirement", f"requirement not satisfied: {requirement['id']}"))

    limit_checks = {item.get("id"): item for item in (cast.get("limits") or [])}
    for limit in spell.get("limits") or []:
        check = limit_checks.get(limit["id"])
        if check is None:
            issues.append(ValidationIssue("limit", f"limit not evaluated: {limit['id']}"))
        elif check.get("status") == "exceeded":
            issues.append(ValidationIssue("limit-exceeded", f"limit exceeded: {limit['id']}"))
        elif check.get("status") not in {"satisfied", "not-applicable"}:
            issues.append(ValidationIssue("limit", f"limit unresolved: {limit['id']}"))

    status = cast.get("status")
    if status == "resolved":
        evidence_ids = {item.get("id") for item in (cast.get("evidence") or [])}
        for requirement in spell["evidence"]["required"]:
            if requirement["id"] not in evidence_ids:
                issues.append(ValidationIssue("evidence-missing", f"missing effect evidence: {requirement['id']}"))
        if "actual_effect" not in cast:
            issues.append(ValidationIssue("effect-missing", "resolved cast must record actual_effect"))

    # Blocking is allowed to contain missing requirements/telemetry by design.
    if status == "blocked":
        issues = [
            issue
            for issue in issues
            if issue.code
            not in {
                "telemetry-missing",
                "telemetry-stale",
                "requirement",
                "limit",
                "limit-exceeded",
            }
        ]

    return issues


def cast_can_proceed(spell: dict[str, Any], cast: dict[str, Any]) -> bool:
    """Return True only when the cast is ready to enter effectful execution."""

    if cast.get("status") not in {"ready", "casting", "resolved"}:
        return False
    return not validate_cast(spell, cast)


def make_receipt(spell: dict[str, Any], cast: dict[str, Any], standing: Standing | None = None) -> dict[str, Any]:
    """Build a compact inspectable receipt from terminal cast state."""

    if cast.get("status") not in {"blocked", "resolved", "failed"}:
        raise ValueError("receipt requires terminal cast status")

    receipt: dict[str, Any] = {
        "cast_id": cast["cast_id"],
        "spell": dict(cast["spell"]),
        "caster": cast.get("caster"),
        "familiars": cast.get("familiars", []),
        "target": cast.get("target"),
        "intent": cast["intent"],
        "expression": cast["expression"],
        "telemetry_used": [item.get("id") for item in cast.get("telemetry", [])],
        "requirements_applied": [item.get("id") for item in cast.get("requirements", [])],
        "limits_applied": [item.get("id") for item in cast.get("limits", [])],
        "energy_committed": (cast.get("energy") or {}).get("committed", {}),
        "effect": cast.get("actual_effect"),
        "evidence": [
            {key: value for key, value in item.items() if key != "id"}
            for item in cast.get("evidence", [])
        ],
        "residuals": cast.get("residuals", []),
        "status": cast["status"],
    }

    if standing is not None:
        if standing.kind == "spell":
            receipt["standing"] = {
                "demonstrated_level": standing.demonstrated_level,
                "grade": standing.grade,
                "rubric": "spell-protocol-v0",
            }
        else:
            receipt["standing"] = {
                "trick": standing.trick,
                "grade": standing.grade,
                "rubric": "spell-protocol-v0",
            }

    return receipt
