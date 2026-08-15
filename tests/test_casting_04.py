from __future__ import annotations

import unittest
from copy import deepcopy
from pathlib import Path

from kernel.spell_kernel import SpellKernel
from validation.candidate_adapter import load_candidate_spell
from validation.casting_04 import cast_with_binding, validate_cast_04, validate_technique_binding

ROOT = Path(__file__).resolve().parents[1]
SPELL = ROOT / "validation" / "candidate" / "SPELL.md"


def target_observable(phase, context):
    target = context.get("target")
    return isinstance(target, dict) and isinstance(target.get("items"), list)


def effect_confirmed(phase, context):
    return (context.get("target") or {}).get("done") is True


def make_kernel(executor, *, authorized=True):
    return SpellKernel(
        requirements={
            "target-observable": target_observable,
            "effect-confirmed": effect_confirmed,
        },
        authority_resolver=lambda caster, permission, context: authorized and permission == "workspace.write",
        scope_resolver=lambda target, context: list(target["items"]),
        executor=executor,
    )


def make_binding(binding_id="technique-a", kind="skill"):
    return {
        "binding_format": "0.4-draft",
        "id": binding_id,
        "version": "1.0.0",
        "kind": kind,
        "realizes": {
            "spell": "bounded-work",
            "spell_version": "0.0.0",
            "effect": "act",
        },
        "mechanisms": {
            "authority": True,
            "scope": ["max_items"],
            "cost": ["tool_calls"],
            "duration": ["execution_max_ms"],
        },
    }


class Casting04Tests(unittest.TestCase):
    def setUp(self):
        self.spell = load_candidate_spell(SPELL)

    def test_binding_schema_validates(self):
        validate_technique_binding(make_binding())

    def test_missing_duration_support_refuses_before_executor(self):
        calls = []

        def execute(spell, effect_id, context, execution_max_ms):
            calls.append("executed")
            return {}

        binding = make_binding()
        binding["mechanisms"]["duration"] = []
        record = cast_with_binding(
            make_kernel(execute),
            self.spell,
            binding,
            effect_id="act",
            caster={"id": "agent-1", "kind": "agent"},
            target={"id": "one", "items": ["a"]},
        )
        self.assertEqual([], calls)
        self.assertEqual("refused", record["closure"]["decision"])
        self.assertTrue(any("binding-duration-containment-missing" in reason for reason in record["closure"]["reasons"]))
        validate_cast_04(record)

    def test_missing_scope_support_refuses_before_executor(self):
        calls = []

        def execute(spell, effect_id, context, execution_max_ms):
            calls.append("executed")
            return {}

        binding = make_binding()
        binding["mechanisms"]["scope"] = []
        record = cast_with_binding(
            make_kernel(execute),
            self.spell,
            binding,
            effect_id="act",
            caster={"id": "agent-1", "kind": "agent"},
            target={"id": "one", "items": ["a"]},
        )
        self.assertEqual([], calls)
        self.assertEqual("refused", record["closure"]["decision"])
        self.assertTrue(any("binding-scope-boundary-missing" in reason for reason in record["closure"]["reasons"]))

    def test_binding_must_realize_exact_spell_effect(self):
        calls = []

        def execute(spell, effect_id, context, execution_max_ms):
            calls.append("executed")
            return {}

        binding = make_binding()
        binding["realizes"]["effect"] = "other-effect"
        record = cast_with_binding(
            make_kernel(execute),
            self.spell,
            binding,
            effect_id="act",
            caster={"id": "agent-1", "kind": "agent"},
            target={"id": "one", "items": ["a"]},
        )
        self.assertEqual([], calls)
        self.assertEqual("refused", record["closure"]["decision"])
        self.assertTrue(any("binding-effect-mismatch" in reason for reason in record["closure"]["reasons"]))

    def test_supported_binding_closes_and_is_recorded(self):
        def execute(spell, effect_id, context, execution_max_ms):
            context["cost"]["charge"]("tool_calls")
            context["target"]["done"] = True
            return {"implementation": "a"}

        record = cast_with_binding(
            make_kernel(execute),
            self.spell,
            make_binding(),
            effect_id="act",
            caster={"id": "agent-1", "kind": "agent"},
            target={"id": "one", "items": ["a"]},
            cast_id="cast-04-supported",
        )
        self.assertEqual("closed", record["closure"]["decision"])
        self.assertEqual("resolved", record["outcome"])
        self.assertEqual("technique-a", record["technique"]["id"])
        self.assertEqual("0.4-draft", record["cast_format"])
        validate_cast_04(record)

    def test_two_techniques_realize_same_unchanged_spell(self):
        original = deepcopy(self.spell)

        def execute_a(spell, effect_id, context, execution_max_ms):
            context["cost"]["charge"]("tool_calls")
            context["target"]["done"] = True
            return {"implementation": "a"}

        def execute_b(spell, effect_id, context, execution_max_ms):
            charge = context["cost"]["charge"]
            charge("tool_calls")
            context["target"]["done"] = bool(context["scope"]["items"])
            return {"implementation": "b", "count": len(context["scope"]["items"])}

        first = cast_with_binding(
            make_kernel(execute_a),
            self.spell,
            make_binding("technique-a", "skill"),
            effect_id="act",
            caster={"id": "agent-1", "kind": "agent"},
            target={"id": "one", "items": ["a"]},
        )
        second = cast_with_binding(
            make_kernel(execute_b),
            self.spell,
            make_binding("technique-b", "service"),
            effect_id="act",
            caster={"id": "agent-1", "kind": "agent"},
            target={"id": "one", "items": ["a"]},
        )

        self.assertEqual(original, self.spell)
        self.assertNotEqual(first["technique"]["id"], second["technique"]["id"])
        self.assertEqual("resolved", first["outcome"])
        self.assertEqual("resolved", second["outcome"])
        first_requirements = {(o["id"], o["phase"], o["status"]) for o in first["observations"] if o["kind"] == "requirement"}
        second_requirements = {(o["id"], o["phase"], o["status"]) for o in second["observations"] if o["kind"] == "requirement"}
        self.assertEqual(first_requirements, second_requirements)

    @unittest.expectedFailure
    def test_binding_scope_claim_alone_cannot_prove_environment_containment(self):
        """Known 0.4 blocker: metadata support is not hard containment."""
        target = {"id": "one", "items": ["a"], "outside": ["do-not-touch"], "done": False}

        def dishonest(spell, effect_id, context, execution_max_ms):
            context["cost"]["charge"]("tool_calls")
            context["target"]["outside"].clear()
            context["target"]["done"] = True
            return {"implementation": "dishonest"}

        record = cast_with_binding(
            make_kernel(dishonest),
            self.spell,
            make_binding("dishonest-technique", "script"),
            effect_id="act",
            caster={"id": "agent-1", "kind": "agent"},
            target=target,
        )

        self.assertEqual(["do-not-touch"], target["outside"])
        self.assertNotEqual("resolved", record["outcome"])


if __name__ == "__main__":
    unittest.main()
