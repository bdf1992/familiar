"""Construct and validate a Familiar View.

A View represents one exact accepted Familiar revision. Schema validity alone
does not establish that provenance: a hand-built object can carry any
`subject` block it likes. `build_view` therefore takes a store and a
`FamiliarRef` and resolves the artifact through it, so the subject block
describes a revision that was actually produced rather than one that was
merely claimed.

Omission is accounted for rather than trusted. The caller names what to
represent; what remains is derived, so a View that silently drops a category
cannot be built.
"""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, Iterable

import jsonschema

VIEW_SCHEMA = Path(__file__).with_name("familiar-view.schema.json")

#: Every guidance category a source Familiar carries. All five are required by
#: `familiar.schema.json`, so a valid Familiar always has all of them and
#: "the source did not have one" is never an explanation for a gap in a View.
SOURCE_CATEGORIES = ("dialect", "attention", "preferences", "stake", "advisory_authority")

VIEW_FORMAT = "0.1"


class FamiliarViewError(ValueError):
    pass


def _load_schema() -> dict[str, Any]:
    return json.loads(VIEW_SCHEMA.read_text(encoding="utf-8"))


def _project(familiar: dict[str, Any], category: str) -> Any:
    """Represent one source category in View shape.

    `dialect` is an object in the source and a string in a View, because a View
    may summarize or translate. Everything else carries across as-is.
    """
    if category == "dialect":
        return familiar["dialect"]["description"]
    return deepcopy(familiar[category])


def validate_view(view: dict[str, Any]) -> None:
    """Validate a View structurally and restate the accounting failure clearly.

    The schema already refuses an unaccounted or double-accounted category. The
    second pass exists so the error names the category instead of reporting a
    failed `oneOf`, which is the difference between a usable message and a
    puzzle.
    """
    schema = _load_schema()
    jsonschema.Draft202012Validator.check_schema(schema)
    try:
        jsonschema.validate(instance=view, schema=schema)
    except jsonschema.ValidationError as error:
        represented = set((view or {}).get("guidance", {}) or {})
        omitted = set((view or {}).get("omitted", []) or [])
        both = sorted(represented & omitted)
        if both:
            raise FamiliarViewError(
                f"View both represents and omits: {', '.join(both)}"
            ) from error
        unaccounted = sorted(set(SOURCE_CATEGORIES) - represented - omitted)
        if unaccounted:
            raise FamiliarViewError(
                f"View does not account for source guidance: {', '.join(unaccounted)}"
            ) from error
        raise FamiliarViewError(str(error)) from error


def build_view(
    store: Any,
    ref: Any,
    *,
    policy: str,
    audience: str,
    represent: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Build a View of the exact revision `ref` names.

    `store.resolve(ref)` establishes provenance. A stale, forged, or
    unretained ref raises there, before any View exists to be trusted.

    `represent` names the categories to carry. Omission is the complement, so
    it is derived rather than supplied and cannot disagree with what was
    represented. Passing None represents everything.
    """
    for name, value in (("policy", policy), ("audience", audience)):
        if not isinstance(value, str) or not value:
            raise FamiliarViewError(f"View perspective requires {name}")

    if represent is None:
        selected = list(SOURCE_CATEGORIES)
    else:
        selected = list(dict.fromkeys(represent))
        unknown = [name for name in selected if name not in SOURCE_CATEGORIES]
        if unknown:
            raise FamiliarViewError(f"not a source guidance category: {', '.join(sorted(unknown))}")

    familiar = store.resolve(ref)

    view = {
        "view_format": VIEW_FORMAT,
        "subject": {
            "id": ref.id,
            "caster_id": ref.caster_id,
            "revision": ref.revision,
            "digest": ref.digest,
        },
        "perspective": {"policy": policy, "for": audience},
        "guidance": {name: _project(familiar, name) for name in SOURCE_CATEGORIES if name in selected},
        "omitted": [name for name in SOURCE_CATEGORIES if name not in selected],
    }
    validate_view(view)
    return view
