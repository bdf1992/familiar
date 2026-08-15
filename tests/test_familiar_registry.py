import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from runtime.familiar_registry import (
    FamiliarConflict,
    FamiliarIdentityChangeForbidden,
    FileFamiliarRegistry,
)


ROOT = Path(__file__).resolve().parents[1]


def load_owl():
    with (ROOT / "spells" / "familiar" / "familiars" / "owl.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)


class FamiliarRegistryTests(unittest.TestCase):
    def test_save_and_load_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = FileFamiliarRegistry(tmp)
            owl = load_owl()
            revision = registry.save(owl)
            loaded, loaded_revision = registry.load("owl.system")
            self.assertEqual(owl, loaded)
            self.assertEqual(revision, loaded_revision)

    def test_expression_can_develop_without_identity_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = FileFamiliarRegistry(tmp)
            owl = load_owl()
            revision = registry.save(owl)
            changed = deepcopy(owl)
            changed["expression"]["language"].append("trial")
            new_revision = registry.save(changed, expected_revision=revision)
            self.assertNotEqual(revision, new_revision)

    def test_familiar_cannot_replace_its_own_form(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = FileFamiliarRegistry(tmp)
            owl = load_owl()
            revision = registry.save(owl)
            changed = deepcopy(owl)
            changed["form"]["name"] = "Stag"
            changed["form"]["glyph"] = "🦌"
            with self.assertRaises(FamiliarIdentityChangeForbidden):
                registry.save(changed, expected_revision=revision)

    def test_holder_authorized_identity_change_can_replace_form(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = FileFamiliarRegistry(tmp)
            owl = load_owl()
            revision = registry.save(owl)
            changed = deepcopy(owl)
            changed["form"]["name"] = "Stag"
            changed["form"]["glyph"] = "🦌"
            new_revision = registry.save(
                changed,
                expected_revision=revision,
                identity_change_authorized=True,
            )
            loaded, _ = registry.load("owl.system")
            self.assertEqual("Stag", loaded["form"]["name"])
            self.assertNotEqual(revision, new_revision)

    def test_stale_revision_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = FileFamiliarRegistry(tmp)
            owl = load_owl()
            revision = registry.save(owl)
            changed = deepcopy(owl)
            changed["history"].append({"kind": "trial", "summary": "first update"})
            registry.save(changed, expected_revision=revision)

            stale = deepcopy(owl)
            stale["history"].append({"kind": "trial", "summary": "stale update"})
            with self.assertRaises(FamiliarConflict):
                registry.save(stale, expected_revision=revision)


if __name__ == "__main__":
    unittest.main()
