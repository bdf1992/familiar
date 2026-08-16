"""Authority is enforced through an attenuated execution capability (issue #11).

Authority was resolved before closure while the Technique Binding only
asserted `authority: true`. Nothing proved the executor ran with authority no
broader than the authority that closed the Cast, so preflight authorization
sat in front of an unconstrained effect path -- the same defect Scope had.

`KERNEL.md` already required "an execution path constrained to the resulting
Authority boundary". The specification was right; the runtime did not
implement it.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
import unittest

from environment.authority import (
    AuthorityViolationError,
    RecordingHostCredential,
    attenuated_credential_enforcer,
)
from environment.scope import mapping_scope_enforcer
from kernel.spell_kernel import SpellKernel
from validation.candidate_adapter import load_candidate_spell
from validation.casting_04 import cast_with_binding

ROOT = Path(__file__).resolve().parents[1]
SPELL = ROOT / "validation" / "candidate" / "SPELL.md"

ADMISSIBLE_KEYS = ("id", "items", "done", "valid")


class BroadHostCredential:
    """A host credential that can reach far more than any one Cast resolves.

    This is the realistic case: the process holds an ambient token good for the
    whole workspace, and the question is whether the Technique inherits it.
    """

    def __init__(self):
        self.acts = []

    def act(self, permission, resource=None, **kwargs):
        self.acts.append((permission, resource))
        return {"permission": permission, "resource": resource}


def target_observable(phase, context):
    target = context.get("target")
    return isinstance(target, Mapping) and isinstance(target.get("items"), list)


def effect_confirmed(phase, context):
    return (context.get("target") or {}).get("done") is True


def binding(binding_id="authority-technique"):
    return {
        "binding_format": "0.4-draft",
        "id": binding_id,
        "version": "1.0.0",
        "kind": "service",
        "realizes": {"spell": "bounded-work", "spell_version": "0.0.0", "effect": "act"},
        "mechanisms": {
            "authority": True,
            "scope": ["max_items"],
            "cost": ["tool_calls"],
            "duration": ["execution_max_ms"],
        },
    }


def make_kernel(executor, *, host=None, resources=None, enforce_authority=True):
    enforcer = None
    if enforce_authority:
        enforcer = attenuated_credential_enforcer(host or BroadHostCredential(), resources=resources)
    return SpellKernel(
        requirements={"target-observable": target_observable, "effect-confirmed": effect_confirmed},
        authority_resolver=lambda caster, permission, context: permission == "workspace.write",
        authority_enforcer=enforcer,
        scope_resolver=lambda target, context: list(target["items"]),
        scope_enforcer=mapping_scope_enforcer(ADMISSIBLE_KEYS),
        executor=executor,
    )


def run(kernel, spell, target=None):
    return cast_with_binding(
        kernel,
        spell,
        binding(),
        effect_id="act",
        caster={"id": "agent-1", "kind": "agent"},
        target=target or {"id": "one", "items": ["a"], "done": False},
    )


class AuthorityEnforcementTests(unittest.TestCase):
    def setUp(self):
        self.spell = load_candidate_spell(SPELL)

    def test_in_authority_execution_still_succeeds_through_the_credential(self):
        host = BroadHostCredential()

        def honest(spell, effect_id, context, execution_max_ms):
            context["cost"]["charge"]("tool_calls")
            context["authority"].act("workspace.write", "a")
            context["target"]["done"] = True
            return {"implementation": "honest"}

        record = run(make_kernel(honest, host=host), self.spell)

        self.assertEqual("resolved", record["outcome"])
        self.assertEqual([("workspace.write", "a")], host.acts)

    def test_a_permission_beyond_the_resolved_authority_cannot_reach_the_host(self):
        host = BroadHostCredential()

        def overreaching(spell, effect_id, context, execution_max_ms):
            context["cost"]["charge"]("tool_calls")
            context["target"]["done"] = True
            context["authority"].act("registry.write", "someone-elses-book")
            return {"implementation": "overreaching"}

        record = run(make_kernel(overreaching, host=host), self.spell)

        self.assertEqual([], host.acts)
        self.assertNotEqual("resolved", record["outcome"])

    def test_a_resource_beyond_the_resolved_authority_cannot_reach_the_host(self):
        """Preflight permits one resource; the host credential can affect another."""
        host = BroadHostCredential()

        def overreaching(spell, effect_id, context, execution_max_ms):
            context["cost"]["charge"]("tool_calls")
            context["authority"].act("workspace.write", "a")
            context["target"]["done"] = True
            context["authority"].act("workspace.write", "outside-the-cast")
            return {"implementation": "overreaching"}

        record = run(make_kernel(overreaching, host=host, resources=("a",)), self.spell)

        self.assertEqual([("workspace.write", "a")], host.acts)
        self.assertNotEqual("resolved", record["outcome"])

    def test_a_swallowed_authority_violation_is_still_attributable(self):
        host = BroadHostCredential()

        def sneaky(spell, effect_id, context, execution_max_ms):
            context["cost"]["charge"]("tool_calls")
            try:
                context["authority"].act("registry.write", "someone-elses-book")
            except AuthorityViolationError:
                pass
            context["target"]["done"] = True
            return {"implementation": "sneaky"}

        record = run(make_kernel(sneaky, host=host), self.spell)

        self.assertEqual([], host.acts)
        self.assertEqual("failed", record["outcome"])
        after = next(
            item for item in record["observations"]
            if item["id"] == "authority-enforcement" and item["phase"] == "after"
        )
        self.assertEqual("violated", after["status"])
        self.assertEqual(
            [{"permission": "registry.write", "resource": "someone-elses-book"}],
            after["value"]["violations"],
        )
        self.assertTrue(any("authority violated" in item for item in record["residuals"]))

    def test_cast_records_the_authority_requirement_and_the_enforcing_mechanism(self):
        def honest(spell, effect_id, context, execution_max_ms):
            context["cost"]["charge"]("tool_calls")
            context["target"]["done"] = True
            return {}

        record = run(make_kernel(honest, resources=("a",)), self.spell)

        before = next(
            item for item in record["observations"]
            if item["id"] == "authority-enforcement" and item["phase"] == "before"
        )
        self.assertEqual("satisfied", before["status"])
        self.assertEqual(["workspace.write"], before["value"]["resolved"])
        enforcement = before["value"]["enforcement"]
        self.assertEqual("environment.attenuated-credential", enforcement["mechanism"])
        self.assertEqual(["workspace.write"], enforcement["granted"])
        self.assertEqual(["a"], enforcement["resources"])
        # The declared Authority Requirement is still recorded in its own right.
        self.assertEqual(
            "satisfied",
            next(item for item in record["observations"] if item["id"] == "write-authority")["status"],
        )

    def test_closure_refuses_when_no_attenuated_capability_can_be_supplied(self):
        calls = []

        def never(spell, effect_id, context, execution_max_ms):
            calls.append("executed")
            return {}

        record = run(make_kernel(never, enforce_authority=False), self.spell)

        self.assertEqual([], calls)
        self.assertEqual("refused", record["closure"]["decision"])
        self.assertTrue(
            any("runtime-authority-enforcer-missing" in reason for reason in record["closure"]["reasons"])
        )
        self.assertIsNone(record["outcome"])

    def test_the_attenuated_credential_does_not_expose_the_host_credential(self):
        seen = {}

        def curious(spell, effect_id, context, execution_max_ms):
            context["cost"]["charge"]("tool_calls")
            credential = context["authority"]
            seen["granted"] = credential.granted
            seen["public"] = [name for name in dir(credential) if not name.startswith("_")]
            context["target"]["done"] = True
            return {}

        record = run(make_kernel(curious, host=BroadHostCredential()), self.spell)

        self.assertEqual("resolved", record["outcome"])
        self.assertEqual(("workspace.write",), seen["granted"])
        # act() and granted are the whole public surface. Widening back to the
        # host credential is not reachable without touching private state.
        self.assertEqual(["act", "granted"], sorted(seen["public"]))


class AttenuatedCredentialUnitTests(unittest.TestCase):
    def test_a_denied_act_raises_and_is_recorded_once(self):
        from environment.authority import AttenuatedCredentialBoundary

        host = BroadHostCredential()
        boundary = AttenuatedCredentialBoundary(host, ("workspace.write",), resources=("a",))
        credential = boundary.handle()

        credential.act("workspace.write", "a")
        with self.assertRaises(AuthorityViolationError):
            credential.act("registry.write", "a")
        with self.assertRaises(AuthorityViolationError):
            credential.act("workspace.write", "b")

        self.assertEqual([("workspace.write", "a")], host.acts)
        self.assertEqual(2, len(boundary.violations()))

    def test_a_host_credential_without_act_is_refused_at_construction(self):
        from environment.authority import AttenuatedCredentialBoundary

        with self.assertRaises(TypeError):
            AttenuatedCredentialBoundary(object(), ("workspace.write",))

    def test_the_recording_host_credential_records_what_passed_attenuation(self):
        host = RecordingHostCredential()
        boundary = attenuated_credential_enforcer(host)({"id": "a"}, ["workspace.write"], {})
        boundary.handle().act("workspace.write", "a")
        with self.assertRaises(AuthorityViolationError):
            boundary.handle().act("registry.write", "a")
        self.assertEqual([("workspace.write", "a")], host.acts)


if __name__ == "__main__":
    unittest.main()
