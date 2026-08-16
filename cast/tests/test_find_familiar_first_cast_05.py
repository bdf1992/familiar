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
    def test_accepted_candidate_persists_and_resolves_through_invariant_cast(self):
        spell = load_candidate_spell(EXAMPLE / "SPELL.md")
        binding = json.loads((EXAMPLE / "binding.json").read_text(encoding="utf-8"))
        validate_technique_binding(binding)
        accepted = candidate()
        validate_familiar(accepted)

        with tempfile.TemporaryDirectory() as tmp:
            store = FamiliarStore(Path(tmp) / "familiars")
            result_ref: FamiliarRef | None = None

            def caster_resolved(phase, context):
                caster = context.get("caster") or {}
                return caster.get("id") == "bdo" and caster.get("kind") == "human"

            def familiar_store_supported(phase, context):
                return store.root is not None

            def familiar_valid(phase, context):
                try:
                    validate_familiar(accepted)
                except Exception:
                    return False
                return True

            def caster_accepted(phase, context):
                return context.get("target", {}).get("accepted") is True

            def familiar_persisted(phase, context):
                if result_ref is None:
                    return False
                return store.resolve(result_ref) == accepted

            def execute(spell_value, effect_id, context, execution_max_ms):
                nonlocal result_ref
                result_ref = store.put(accepted, caster_id=context["caster"]["id"])
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
                    "caster-resolved": caster_resolved,
                    "familiar-store-supported": familiar_store_supported,
                    "familiar-valid": familiar_valid,
                    "caster-accepted": caster_accepted,
                    "familiar-persisted": familiar_persisted,
                },
                executor=execute,
            )

            record = cast_with_binding(
                kernel,
                spell,
                binding,
                effect_id="establish",
                caster={"id": "bdo", "kind": "human"},
                target={"caster": "bdo", "accepted": True},
                cast_id="cast-find-bdo-first",
            )

            self.assertEqual("closed", record["closure"]["decision"])
            self.assertEqual("resolved", record["outcome"])
            self.assertIsNotNone(result_ref)
            assert result_ref is not None
            self.assertEqual(accepted, FamiliarStore(Path(tmp) / "familiars").resolve(result_ref))

    def test_unaccepted_candidate_refuses_before_persistence(self):
        spell = load_candidate_spell(EXAMPLE / "SPELL.md")
        binding = json.loads((EXAMPLE / "binding.json").read_text(encoding="utf-8"))
        accepted = candidate()

        with tempfile.TemporaryDirectory() as tmp:
            store = FamiliarStore(Path(tmp) / "familiars")
            executions: list[str] = []

            def execute(spell_value, effect_id, context, execution_max_ms):
                executions.append("entered")
                return {}

            kernel = SpellKernel(
                requirements={
                    "caster-resolved": lambda phase, context: True,
                    "familiar-store-supported": lambda phase, context: True,
                    "familiar-valid": lambda phase, context: True,
                    "caster-accepted": lambda phase, context: context.get("target", {}).get("accepted") is True,
                    "familiar-persisted": lambda phase, context: False,
                },
                executor=execute,
            )

            record = cast_with_binding(
                kernel,
                spell,
                binding,
                effect_id="establish",
                caster={"id": "bdo", "kind": "human"},
                target={"caster": "bdo", "accepted": False},
            )

            # caster-accepted is an after Requirement in the current declaration,
            # so execution may occur but the Effect must not resolve. This test
            # makes that current semantics explicit rather than pretending
            # acceptance is a before-closure gate in the runtime declaration.
            self.assertNotEqual("resolved", record["outcome"])
            self.assertEqual(["entered"], executions)


if __name__ == "__main__":
    unittest.main()
