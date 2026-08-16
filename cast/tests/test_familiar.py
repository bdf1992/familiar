import json
import unittest

from kernel.resources import FAMILIAR_SCHEMA, OWL_PATH
from kernel.spell_kernel import validate_familiar


class FamiliarFoundationTests(unittest.TestCase):
    def test_owl_uses_the_same_familiar_schema(self):
        owl = json.loads(OWL_PATH.read_text(encoding="utf-8"))
        validate_familiar(owl)
        self.assertEqual("0.3", owl["familiar_format"])
        self.assertEqual("owl.agent", owl["caster"]["id"])
        self.assertEqual("agent", owl["caster"]["kind"])
        self.assertIn("advisory_authority", owl)
        self.assertNotIn("authority", owl)

    def test_familiar_schema_does_not_grant_runtime_authority(self):
        schema = json.loads(FAMILIAR_SCHEMA.read_text(encoding="utf-8"))
        properties = schema["properties"]
        self.assertIn("advisory_authority", properties)
        self.assertNotIn("authority", properties)


if __name__ == "__main__":
    unittest.main()
