from __future__ import annotations

import unittest
from copy import deepcopy
from pathlib import Path

from kernel.spell_kernel import SpellKernel
from validation.candidate_adapter import load_candidate_spell
from validation.casting_04 import cast_with_binding

ROOT = Path(__file__).resolve().parents[1]
SPELL = ROOT / "validation" / "candidate" / "SPELL.md"


def binding():
    return {
        "binding_format": "0.4-draft",
        "id": "material-technique",
        "version": "1.0.0",
        "kind": "service",
        "realizes": {
            "spell": "bounded-work",
            "spell_version": "0.0.0",
            "effect": "act",
        },
        "mechanisms": {
            "authority": True,
            "scope": ["max_items"],
            "cost": ["crystal"],
            "duration": ["execution_max_ms"],
        },
    }


class CastingOrder04Tests(unittest.TestCase):
    def setUp(self):
        self.spell = load_candidate_spell(SPELL)
        effect = self.spell["effects"][0]
        effect["requirements"]["before"].append(
            {"id": "material-available", "description": "One crystal is available before closure."}
        )
        cost = next(item for item in effect["requirements"]["during"] if "cost" in item)
        cost["cost"]["resource"] = "crystal"
        cost["id"] = "material-cost"

    def make_kernel(self, inventory, actions):
        def target_observable(phase, context):
            target = context.get("target") or {}
            return target.get("valid") is True

        def material_available(phase, context):
            return inventory["crystal"] >= 1

        def effect_confirmed(phase, context):
            return (context.get("target") or {}).get("done") is True

        def execute(spell, effect_id, context, execution_max_ms):
            actions.append("executor-entered")
            context["cost"]["charge"]("crystal")
            inventory["crystal"] -= 1
            actions.append("crystal-consumed")
            context["target"]["done"] = True
            return {"done": True}

        return SpellKernel(
            requirements={
                "target-observable": target_observable,
                "material-available": material_available,
                "effect-confirmed": effect_confirmed,
            },
            authority_resolver=lambda caster, permission, context: permission == "workspace.write",
            scope_resolver=lambda target, context: list(target["items"]),
            executor=execute,
        )

    def test_invalid_target_refuses_before_material_is_consumed(self):
        inventory = {"crystal": 1}
        actions = []
        target = {"id": "bad", "valid": False, "items": ["a"], "done": False}

        record = cast_with_binding(
            self.make_kernel(inventory, actions),
            self.spell,
            binding(),
            effect_id="act",
            caster={"id": "caster-1", "kind": "human"},
            target=target,
        )

        self.assertEqual("refused", record["closure"]["decision"])
        self.assertEqual(1, inventory["crystal"])
        self.assertEqual([], actions)

    def test_missing_material_refuses_before_executor(self):
        inventory = {"crystal": 0}
        actions = []
        target = {"id": "good", "valid": True, "items": ["a"], "done": False}

        record = cast_with_binding(
            self.make_kernel(inventory, actions),
            self.spell,
            binding(),
            effect_id="act",
            caster={"id": "caster-1", "kind": "human"},
            target=target,
        )

        self.assertEqual("refused", record["closure"]["decision"])
        self.assertEqual(0, inventory["crystal"])
        self.assertEqual([], actions)
        self.assertTrue(any("material-available" in reason for reason in record["closure"]["reasons"]))

    def test_valid_cast_consumes_material_only_after_closure(self):
        inventory = {"crystal": 1}
        actions = []
        target = {"id": "good", "valid": True, "items": ["a"], "done": False}

        record = cast_with_binding(
            self.make_kernel(inventory, actions),
            self.spell,
            binding(),
            effect_id="act",
            caster={"id": "caster-1", "kind": "human"},
            target=target,
            cast_id="cast-material-order",
        )

        self.assertEqual("closed", record["closure"]["decision"])
        self.assertEqual("resolved", record["outcome"])
        self.assertEqual(0, inventory["crystal"])
        self.assertEqual(["executor-entered", "crystal-consumed"], actions)
        material = next(item for item in record["observations"] if item["id"] == "material-cost")
        self.assertEqual("during", material["phase"])
        self.assertEqual("satisfied", material["status"])
        self.assertEqual(1, material["value"]["used"])


if __name__ == "__main__":
    unittest.main()
