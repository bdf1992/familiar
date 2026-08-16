"""FORMAT 0.3 exists in two incompatible generations (issue #55).

The Spell domain owns declaration format. It publishes
``spell/format/0.3-draft/spell.schema.json``, generated from
``spell/format/0.3-draft/models.py``. Nothing at runtime loads it.

The Cast domain admits declarations using its own
``cast/validation/candidate/spell.schema.json``, and that is the schema every
cast in this repository is actually admitted by.

These are not two copies of one document that drifted. They describe different
Requirement models, and neither accepts the other's declarations:

    generation      spell_format        a Requirement is
    ------------    ----------------    ---------------------------------------
    Cast domain     "0.3-candidate"     {id} plus one typed key -- description,
                                        authority, scope, or cost
    Spell domain    "0.3"               {id, check, binding, ...} -- every
                                        Requirement names the check that
                                        discharges it and the binding selector

The Spell generation anticipated where the Kernel actually went: #13 bound
Requirements to exact capability receipts by typed demand, and #32 compiled them
into obligations with declared discharge mechanisms. ``check`` and ``binding``
are those ideas in the declaration. The Cast generation was frozen before that.

**These tests document a defect as running code rather than as prose.** They are
not a specification of desired behavior, and passing them is not a claim that
the fork is acceptable. They exist so the fork cannot widen unnoticed and so
that whoever closes #55 finds out immediately when the divergence changes shape.

Every assertion here is expected to change when #55 closes. That is the point.
"""

from __future__ import annotations

import json
from pathlib import Path
import unittest

import jsonschema
import yaml

from kernel.resources import REPO_ROOT

CAST_ADMISSION_SCHEMA = REPO_ROOT / "cast" / "validation" / "candidate" / "spell.schema.json"
SPELL_CANONICAL_SCHEMA = REPO_ROOT / "spell" / "format" / "0.3-draft" / "spell.schema.json"
SPELL_CANONICAL_EXAMPLE = (
    REPO_ROOT / "spell" / "format" / "0.3-draft" / "examples" / "find-familiar.SPELL.md"
)


def load_schema(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def frontmatter(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end < 0:
        return None
    data = yaml.safe_load(text[4:end])
    return data if isinstance(data, dict) else None


def declarations_admitted_by_cast() -> list[tuple[Path, dict]]:
    """Every declaration the Cast domain currently admits as 0.3."""
    found = []
    for path in sorted(REPO_ROOT.rglob("*SPELL*.md")):
        if ".agent-spells-local" in path.parts:
            continue
        data = frontmatter(path)
        if data and str(data.get("spell_format", "")) == "0.3-candidate":
            found.append((path, data))
    return found


def errors_against(schema: dict, instance: dict) -> list[jsonschema.ValidationError]:
    validator = jsonschema.Draft202012Validator(schema)
    return sorted(validator.iter_errors(instance), key=lambda error: list(error.path))


class TwoFormatGenerationsTests(unittest.TestCase):
    def setUp(self):
        self.cast_schema = load_schema(CAST_ADMISSION_SCHEMA)
        self.spell_schema = load_schema(SPELL_CANONICAL_SCHEMA)
        self.admitted = declarations_admitted_by_cast()

    def test_the_repository_actually_casts_declarations(self):
        """A fork with no declarations on either side would not be worth pinning."""
        self.assertGreater(
            len(self.admitted),
            0,
            "no 0.3-candidate declarations found; this test knows nothing about the tree",
        )

    def test_every_cast_declaration_is_admitted_by_the_cast_schema(self):
        """The baseline: what runs today, runs."""
        for path, data in self.admitted:
            with self.subTest(declaration=path.name):
                jsonschema.validate(instance=data, schema=self.cast_schema)

    def test_every_cast_declaration_is_refused_by_the_spell_schema(self):
        """The defect, stated exactly.

        The domain that owns declaration format would refuse every declaration
        this repository casts. Pointing the adapter at the canonical schema
        without migrating declarations would therefore refuse all of them --
        which is why #55 cannot be closed by deleting the Cast copy.
        """
        for path, data in self.admitted:
            with self.subTest(declaration=path.name):
                errors = errors_against(self.spell_schema, data)
                self.assertNotEqual(
                    [],
                    errors,
                    f"{path.name} is now accepted by the canonical schema; "
                    "the fork has changed shape and #55 needs re-reading",
                )

    def test_the_refusal_is_about_check_and_binding_not_incidental(self):
        """Name the disagreement rather than recording that one exists.

        A test asserting only 'these differ' would still pass if they came to
        differ for an entirely unrelated reason, and would say nothing useful
        to whoever closes this.
        """
        for path, data in self.admitted:
            with self.subTest(declaration=path.name):
                messages = " ".join(e.message for e in errors_against(self.spell_schema, data))
                self.assertIn("check", messages)
                self.assertIn("binding", messages)

    def test_the_spell_example_is_refused_by_the_cast_schema(self):
        """The fork runs both ways; neither generation is a superset."""
        data = frontmatter(SPELL_CANONICAL_EXAMPLE)
        self.assertIsNotNone(data)
        errors = errors_against(self.cast_schema, data)
        self.assertNotEqual([], errors, "the Cast schema now accepts the canonical example")
        messages = " ".join(e.message for e in errors)
        self.assertIn("Additional properties are not allowed", messages)

    def test_the_two_generations_declare_different_spell_format_values(self):
        """`0.3-candidate` and `0.3` are different formats wearing one number.

        This is the cheapest way to notice the fork, and it is the reason the
        divergence survived: the version string looks close enough to read as
        one generation.
        """
        cast_format = self.cast_schema["properties"]["spell_format"]
        spell_format = self.spell_schema["properties"]["spell_format"]
        self.assertNotEqual(
            cast_format.get("const", cast_format.get("enum")),
            spell_format.get("const", spell_format.get("enum")),
        )


if __name__ == "__main__":
    unittest.main()
