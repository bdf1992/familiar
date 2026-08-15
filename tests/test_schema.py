import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

try:
    import jsonschema
except ImportError:  # Runtime stays dependency-free; CI installs this test dependency.
    jsonschema = None


class SchemaTests(unittest.TestCase):
    def test_all_json_files_parse(self):
        for path in ROOT.rglob("*.json"):
            with self.subTest(path=path.relative_to(ROOT)):
                with path.open("r", encoding="utf-8") as handle:
                    json.load(handle)

    @unittest.skipIf(jsonschema is None, "jsonschema test dependency unavailable")
    def test_familiar_spell_conforms_to_spell_schema(self):
        with (ROOT / "protocol" / "spell.schema.json").open("r", encoding="utf-8") as handle:
            schema = json.load(handle)
        with (ROOT / "spells" / "familiar" / "SPELL.json").open("r", encoding="utf-8") as handle:
            familiar_spell = json.load(handle)
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.validate(instance=familiar_spell, schema=schema)

    @unittest.skipIf(jsonschema is None, "jsonschema test dependency unavailable")
    def test_owl_conforms_to_familiar_schema(self):
        with (ROOT / "spells" / "familiar" / "familiar.schema.json").open("r", encoding="utf-8") as handle:
            schema = json.load(handle)
        with (ROOT / "spells" / "familiar" / "familiars" / "owl.json").open("r", encoding="utf-8") as handle:
            owl = json.load(handle)
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.validate(instance=owl, schema=schema)


if __name__ == "__main__":
    unittest.main()
