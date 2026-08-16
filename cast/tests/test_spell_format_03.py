import importlib.util
import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path

import yaml
from pydantic import ValidationError

REPO = Path(__file__).resolve().parents[2]
FORMAT = REPO / "spell" / "format" / "0.3-draft"
SPECIMEN = FORMAT / "examples" / "find-familiar.SPELL.md"
SCHEMA = FORMAT / "spell.schema.json"
MODELS = FORMAT / "models.py"


def load_models():
    spec = importlib.util.spec_from_file_location("spell_format_03_models", MODELS)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_frontmatter(path):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise AssertionError(f"missing YAML frontmatter: {path}")
    frontmatter, _, _ = text[4:].partition("\n---\n")
    if not frontmatter:
        raise AssertionError(f"unterminated YAML frontmatter: {path}")
    return yaml.safe_load(frontmatter)


class SpellFormat03Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.models = load_models()
        cls.specimen = load_frontmatter(SPECIMEN)

    def test_find_familiar_specimen_validates(self):
        spell = self.models.SpellDeclaration.model_validate(self.specimen)
        self.assertEqual("find-familiar", spell.name)
        self.assertEqual(["familiar-store"], spell.runtime.protocols)
        protocol = spell.protocols[0]
        self.assertEqual(["put", "resolve"], [item.id for item in protocol.operations])
        self.assertEqual("familiar-ref", spell.effects[0].interface.result.schema_)

    def test_checked_in_json_schema_is_generated_from_model(self):
        checked_in = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(checked_in, self.models.json_schema())

    def test_operation_only_binding_is_not_a_runtime_contract(self):
        with self.assertRaises(ValidationError):
            self.models.BindingSelector.model_validate({"operation": "write"})

    def test_protocol_binding_must_name_declared_operation(self):
        candidate = deepcopy(self.specimen)
        candidate["effects"][0]["requirements"]["before"][2]["binding"]["operation"] = "delete"
        with self.assertRaises(ValidationError):
            self.models.SpellDeclaration.model_validate(candidate)

    def test_protocol_operation_schema_reference_must_resolve(self):
        candidate = deepcopy(self.specimen)
        candidate["protocols"][0]["operations"][0]["result"]["schema"] = "missing-ref"
        with self.assertRaises(ValidationError):
            self.models.SpellDeclaration.model_validate(candidate)

    def test_scope_cannot_claim_preflight_counting_as_enforcement(self):
        with self.assertRaises(ValidationError):
            self.models.ScopeConstraint.model_validate(
                {"max_items": 2, "enforcement": "preflight"}
            )

    def test_implementation_suggestion_does_not_need_to_be_selected(self):
        candidate = deepcopy(self.specimen)
        candidate["implementations"] = []
        spell = self.models.SpellDeclaration.model_validate(candidate)
        self.assertEqual([], spell.implementations)


if __name__ == "__main__":
    unittest.main()
