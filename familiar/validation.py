from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema

_SCHEMA_PATH = Path(__file__).with_name("familiar.schema.json")


def validate_familiar(familiar: dict[str, Any]) -> None:
    """Validate one Familiar using the Familiar domain's own contract."""
    with _SCHEMA_PATH.open("r", encoding="utf-8") as handle:
        schema = json.load(handle)
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.validate(instance=familiar, schema=schema)
