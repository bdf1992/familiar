from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from familiar.store import FamiliarRef, FamiliarStore
from familiar.validation import validate_familiar
from kernel.spell_kernel import SpellKernel
from validation.candidate_adapter import load_candidate_spell
from validation.casting_04 import cast_with_binding, validate_technique_binding

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "find-familiar"
OWL_PATH = ROOT.parent / "familiar" / "owl" / "owl.json"


def candidate():
    return {
        "familiar_format": "0.3",
        "id": "bdo.familiar",
        "caster": {"id": "bdo", "kind": "human"},
        "dialect": {"description": "Compact distinction-first working language."},
        "attention": ["collapsed distinctions", "conceptual drift"],
        "preferences": ["small inspectable kernels"],
        "stake": ["practitioner agent work"],
        "advisory_authority": [],
    }


class FindFamiliarFirstCast05Tests(unittest.TestCase):
    def test_owl_casts_for_subject_and_subject_familiar_persists(self):
        spell = load_candidate_spell(EXAMPLE / "SPELL.md")
        binding = json.loads((EXAMPLE / "binding.json").read_text(encoding="utf-8"))
        validate_technique_binding(binding)
        owl = json.loads(OWL_PATH.read_text(encoding="utf-8"))
        accepted = candidate()
        validate_familiar(owl)
        validate_familiar(accepted)

        with tempfile.TemporaryDirectory() as tmp:
            store = FamiliarStore(Path(tmp) / "familiars")
            result_ref: FamiliarRef | None = None

            def subject_resolved(phase, context):
                subject = (context.get("target") or {}).get("subject") or {}
                return subject.get("id") == "bdo" and subject.get("kind") == "human"

            def familiar_store_supported(phase, context):
                return store.root is not None

            def familiar_valid(phase, context):
                try:
                    validate_familiar(accepted)
                except Exception:
                    return False
                return True

            def subject_accepted(phase, context):
                return (context.get("target") or {}).get("accepted") is True

            def familiar_persisted(phase, context):
                if result_ref is None:
                    return False
                return store.resolve(result_ref) == accepted

            def execute(spell_value, effect_id, context, execution_max_ms):
                nonlocal result_ref
                subject_id = context["target"]["subject"]["id"]
                result_ref = store.put(accepted, caster_id=subject_id)
                return {
                    "familiar_ref": {
                        "id": result_ref.id,
                        "caster_id": result_ref.caster_id,
                        "revision": result_ref.revision,
                        "digest": result_ref.digest,
                    }
                }

            kernel = SpellKernel(
                requirements={
                    "subject-resolved": subject_resolved,
                    "familiar-store-supported": familiar_store_supported,
                    "familiar-valid": familiar_valid,
                    "subject-accepted": subject_accepted,
                    "familiar-persisted": familiar_persisted,
                },
                executor=execute,
            )

            record = cast_with_binding(
                kernel,
                spell,
                binding,
                effect_id="establish",
                caster={"id": "owl.agent", "kind": "agent"},
                familiar=owl,
                target={"subject": {"id": "bdo", "kind": "human"}, "accepted": True},
                cast_id="cast-find-bdo-first",
            )

            self.assertEqual("owl.agent", record["caster"]["id"])
            self.assertEqual("owl.system", record["familiar"]["id"])
            self.assertEqual("closed", record["closure"]["decision"])
            self.assertEqual("resolved", record["outcome"])
            self.assertIsNotNone(result_ref)
            assert result_ref is not None
            self.assertEqual("bdo", result_ref.caster_id)
            self.assertEqual(accepted, FamiliarStore(Path(tmp) / "familiars").resolve(result_ref))

    def test_unaccepted_subject_refuses_before_persistence(self):
        spell = load_candidate_spell(EXAMPLE / "SPELL.md")
        binding = json.loads((EXAMPLE / "binding.json").read_text(encoding="utf-8"))
        owl = json.loads(OWL_PATH.read_text(encoding="utf-8"))
        executions: list[str] = []

        def execute(spell_value, effect_id, context, execution_max_ms):
            executions.append("entered")
            return {}

        kernel = SpellKernel(
            requirements={
                "subject-resolved": lambda phase, context: True,
                "familiar-store-supported": lambda phase, context: True,
                "familiar-valid": lambda phase, context: True,
                "subject-accepted": lambda phase, context: (context.get("target") or {}).get("accepted") is True,
                "familiar-persisted": lambda phase, context: False,
            },
            executor=execute,
        )

        record = cast_with_binding(
            kernel,
            spell,
            binding,
            effect_id="establish",
            caster={"id": "owl.agent", "kind": "agent"},
            familiar=owl,
            target={"subject": {"id": "bdo", "kind": "human"}, "accepted": False},
        )

        self.assertEqual("refused", record["closure"]["decision"])
        self.assertEqual([], executions)
        self.assertTrue(any("subject-accepted" in reason for reason in record["closure"]["reasons"]))


if __name__ == "__main__":
    unittest.main()
