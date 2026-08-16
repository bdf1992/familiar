"""Resolve Context + Domain Familiarity + optional Subject Familiar as a HandleView.

Issue #67 owns this Work surface. It is knowledge-side composition only:
there is no Cast import, Environment mutation, persistence, capability grant,
or Closure path here.

The central rule is non-flattening. Context and Domain Familiarity remain
separately addressable source objects. Subject Familiar may shape the projected
view, but cannot rewrite either source or introduce runtime authority.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from typing import Any, Mapping


class DomainHandleError(ValueError):
    """One of the Handle inputs is malformed or violates the read-only boundary."""


def _canonical_digest(value: Mapping[str, Any]) -> str:
    material = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + sha256(material.encode("utf-8")).hexdigest()


def _require_mapping(name: str, value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise DomainHandleError(f"{name} must be a mapping")
    return value


def _source_identity(kind: str, source: Mapping[str, Any]) -> dict[str, Any]:
    identity = source.get("identity")
    if not isinstance(identity, Mapping):
        raise DomainHandleError(f"{kind} requires identity")
    for field in ("id", "anchor"):
        if not isinstance(identity.get(field), str) or not identity[field]:
            raise DomainHandleError(f"{kind} identity requires {field}")
    return {
        "kind": kind,
        "id": identity["id"],
        "anchor": identity["anchor"],
        "digest": _canonical_digest(source),
    }


def _subject_projection(subject: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if subject is None:
        return None

    # This resolver does not reinterpret the Familiar contract. It consumes only
    # participant-relative categories already permitted to guide representation.
    caster = subject.get("caster")
    if not isinstance(caster, Mapping) or not isinstance(caster.get("id"), str):
        raise DomainHandleError("subject Familiar requires caster.id")

    advisory = deepcopy(subject.get("advisory_authority", []))
    # Advisory authority is reported as guidance only. The explicit empty
    # runtime_authority field makes the non-grant visible to consumers.
    return {
        "subject_id": caster["id"],
        "dialect": deepcopy(subject.get("dialect")),
        "attention": deepcopy(subject.get("attention", [])),
        "preferences": deepcopy(subject.get("preferences", [])),
        "stake": deepcopy(subject.get("stake", [])),
        "advisory_authority": advisory,
        "runtime_authority": [],
    }


def resolve_domain_handle(
    context: Mapping[str, Any],
    domain_familiar: Mapping[str, Any],
    subject_familiar: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a copy-isolated, read-only-by-contract participant Handle view.

    The return value keeps the two domain sources separate, carries exact
    content digests, preserves disagreements and unknown/unobserved regions, and
    adds at most a participant-relative projection. It deliberately performs no
    reconciliation: conflicting claims remain conflicting claims.
    """

    context = _require_mapping("context", context)
    domain_familiar = _require_mapping("domain_familiar", domain_familiar)
    if subject_familiar is not None:
        subject_familiar = _require_mapping("subject_familiar", subject_familiar)

    context_copy = deepcopy(dict(context))
    familiar_copy = deepcopy(dict(domain_familiar))

    context_identity = _source_identity("context", context_copy)
    familiar_identity = _source_identity("domain-familiarity", familiar_copy)

    if context_identity["anchor"] != familiar_identity["anchor"]:
        raise DomainHandleError(
            "Context and Domain Familiarity must name the same anchor for this Work resolver"
        )

    disagreements = deepcopy(context_copy.get("disagreements", []))
    unknown = deepcopy(context_copy.get("unknown", []))
    unobserved = deepcopy(context_copy.get("unobserved", []))

    for name, value in (
        ("disagreements", disagreements),
        ("unknown", unknown),
        ("unobserved", unobserved),
    ):
        if not isinstance(value, list):
            raise DomainHandleError(f"context {name} must be a list")

    heuristics = deepcopy(familiar_copy.get("heuristics", []))
    if not isinstance(heuristics, list):
        raise DomainHandleError("Domain Familiarity heuristics must be a list")

    return {
        "handle_view_format": "0.1-work",
        "sources": {
            "context": context_identity,
            "domain_familiarity": familiar_identity,
        },
        "context": context_copy,
        "domain_familiarity": familiar_copy,
        "projection": {
            "subject": _subject_projection(subject_familiar),
            "heuristics": heuristics,
        },
        "disagreements": disagreements,
        "unknown": unknown,
        "unobserved": unobserved,
        "affordances": ["inspect", "orient"],
        "runtime_authority": [],
        "effectful": False,
    }
