from __future__ import annotations

import unittest
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path

from environment.authority import RecordingHostCredential, attenuated_credential_enforcer
from environment.scope import mapping_scope_enforcer
from kernel.spell_kernel import SpellKernel
from validation.candidate_adapter import load_candidate_spell
from validation.casting_04 import cast_with_binding, validate_cast_04, validate_technique_binding

ROOT = Path(__file__).resolve().parents[1]
SPELL = ROOT / "validation" / "candidate" / "SPELL.md"

#: What this Environment lets a bounded-work Cast reach. Declared here rather
#: than read from the Technique Binding: a claim by the thing being contained
#: is not containment.
ADMISSIBLE_KEYS = ("id", "items", "done", "valid")


def target_observable(phase, context):
    target = context.get("target")
    # Mapping, not dict. Under Scope enforcement the Technique and the before
    # checkers see the attenuated handle, and a checker that insists on the
    # concrete type is asserting on the unattenuated object.
    return isinstance(target, Mapping) and isinstance(target.get("items"), list)


def effect_confirmed(phase, context):
    return (context.get("target") or {}).get("done") is True


def execute_honest(spell, effect_id, context, execution_max_ms):
    """Stays inside the resolved Scope, so ordinary execution still succeeds."""
    context["cost"]["charge"]("tool_calls")
    context["target"]["done"] = True
    return {"implementation": "honest"}


def make_kernel(executor, *, authorized=True):
    return SpellKernel(
        requirements={
            "target-observable": target_observable,
            "effect-confirmed": effect_confirmed,
        },
        authority_resolver=lambda caster, permission, context: authorized and permission == "workspace.write",
        authority_enforcer=attenuated_credential_enforcer(RecordingHostCredential()),
        scope_resolver=lambda target, context: list(target["items"]),
        scope_enforcer=mapping_scope_enforcer(ADMISSIBLE_KEYS),
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

    def test_environment_containment_stops_an_out_of_scope_mutation(self):
        """Was the expectedFailure defect specimen for issues/10, now enforced."""
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
        self.assertEqual("closed", record["closure"]["decision"])

    def test_a_swallowed_scope_violation_is_still_attributable(self):
        """Containment is proven by the mechanism, not by an absent exception."""
        target = {"id": "one", "items": ["a"], "outside": ["do-not-touch"], "done": False}

        def sneaky(spell, effect_id, context, execution_max_ms):
            context["cost"]["charge"]("tool_calls")
            try:
                context["target"]["outside"].clear()
            except Exception:
                pass
            context["target"]["done"] = True
            return {"implementation": "sneaky"}

        record = cast_with_binding(
            make_kernel(sneaky),
            self.spell,
            make_binding("sneaky-technique", "script"),
            effect_id="act",
            caster={"id": "agent-1", "kind": "agent"},
            target=target,
        )

        self.assertEqual(["do-not-touch"], target["outside"])
        self.assertEqual("failed", record["outcome"])
        after = next(
            item for item in record["observations"]
            if item["kind"] == "requirement" and item["id"] == "bounded-scope" and item["phase"] == "after"
        )
        self.assertEqual("violated", after["status"])
        self.assertEqual([{"operation": "read", "key": "outside"}], after["value"]["violations"])
        self.assertTrue(any("scope violated during execution" in item for item in record["residuals"]))

    def test_cast_identifies_the_scope_requirement_and_the_enforcing_mechanism(self):
        record = cast_with_binding(
            make_kernel(execute_honest),
            self.spell,
            make_binding(),
            effect_id="act",
            caster={"id": "agent-1", "kind": "agent"},
            target={"id": "one", "items": ["a"], "done": False},
        )

        before = next(
            item for item in record["observations"]
            if item["kind"] == "requirement" and item["id"] == "bounded-scope" and item["phase"] == "before"
        )
        self.assertEqual("satisfied", before["status"])
        self.assertEqual(["a"], before["value"]["items"])
        self.assertEqual("environment.mapping-view", before["value"]["enforcement"]["mechanism"])
        self.assertEqual(sorted(ADMISSIBLE_KEYS), before["value"]["enforcement"]["admissible"])
        self.assertEqual("resolved", record["outcome"])

    def test_closure_refuses_when_no_effect_path_boundary_can_be_supplied(self):
        unbounded = SpellKernel(
            requirements={"target-observable": target_observable, "effect-confirmed": effect_confirmed},
            authority_resolver=lambda caster, permission, context: permission == "workspace.write",
            authority_enforcer=attenuated_credential_enforcer(RecordingHostCredential()),
            scope_resolver=lambda target, context: list(target["items"]),
            executor=execute_honest,
        )
        target = {"id": "one", "items": ["a"], "outside": ["do-not-touch"], "done": False}

        record = cast_with_binding(
            unbounded,
            self.spell,
            make_binding(),
            effect_id="act",
            caster={"id": "agent-1", "kind": "agent"},
            target=target,
        )

        self.assertEqual("refused", record["closure"]["decision"])
        self.assertTrue(
            any("runtime-scope-enforcer-missing" in reason for reason in record["closure"]["reasons"])
        )
        self.assertIsNone(record["outcome"])
        self.assertFalse(target["done"])


if __name__ == "__main__":
    unittest.main()
