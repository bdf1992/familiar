import subprocess
import sys
import unittest
from copy import deepcopy
from pathlib import Path

from kernel.spell_kernel import SpellKernel
from validation.candidate_adapter import cast_candidate, load_candidate_spell

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / "validation" / "candidate" / "SPELL.md"


def target_observable(phase, context):
    target = context.get("target")
    return isinstance(target, dict) and isinstance(target.get("items"), list)


def effect_confirmed(phase, context):
    target = context.get("target") or {}
    return target.get("done") is True


def build_kernel(executor, *, authorized=True):
    return SpellKernel(
        requirements={
            "target-observable": target_observable,
            "effect-confirmed": effect_confirmed,
        },
        authority_resolver=lambda caster, permission, context: authorized and permission == "workspace.write",
        scope_resolver=lambda target, context: target["items"],
        executor=executor,
    )


class CandidateRequirementTests(unittest.TestCase):
    def setUp(self):
        self.spell = load_candidate_spell(CANDIDATE)

    def test_candidate_drives_authority_scope_cost_and_duration_without_cast_arguments(self):
        def execute(spell, effect_id, context, execution_max_ms):
            context["cost"]["charge"]("tool_calls")
            context["target"]["done"] = True
            return {"done": True}

        target = {"id": "one", "items": ["a"]}
        record = cast_candidate(
            build_kernel(execute),
            self.spell,
            effect_id="act",
            caster={"id": "agent-1", "kind": "agent"},
            target=target,
            cast_id="candidate-pass",
        )

        self.assertEqual("0.3-candidate", record["cast_format"])
        self.assertEqual("closed", record["closure"]["decision"])
        self.assertEqual("resolved", record["outcome"])
        self.assertEqual(target, record["target"])

        by_id = {item["id"]: item for item in record["observations"]}
        self.assertEqual("satisfied", by_id["write-authority"]["status"])
        self.assertEqual("satisfied", by_id["bounded-scope"]["status"])
        self.assertEqual("satisfied", by_id["tool-budget"]["status"])
        self.assertEqual("during", by_id["tool-budget"]["phase"])
        self.assertEqual("satisfied", by_id["execution-time"]["status"])
        self.assertEqual("during", by_id["execution-time"]["phase"])
        self.assertEqual("satisfied", by_id["effect-confirmed"]["status"])

    def test_candidate_scope_requirement_refuses_before_execution(self):
        calls = []

        def execute(spell, effect_id, context, execution_max_ms):
            calls.append("executed")
            return {}

        record = cast_candidate(
            build_kernel(execute),
            self.spell,
            effect_id="act",
            caster={"id": "agent-1", "kind": "agent"},
            target={"id": "wide", "items": ["a", "b", "c"]},
        )
        self.assertEqual([], calls)
        self.assertEqual("refused", record["closure"]["decision"])
        scope = next(item for item in record["observations"] if item["id"] == "bounded-scope")
        self.assertEqual("violated", scope["status"])

    def test_candidate_cost_requirement_stops_before_excess_action(self):
        spell = deepcopy(self.spell)
        cost = next(item for item in spell["effects"][0]["requirements"]["during"] if "cost" in item)
        cost["cost"]["max"] = 1
        actions = []

        def execute(normalized, effect_id, context, execution_max_ms):
            charge = context["cost"]["charge"]
            charge("tool_calls")
            actions.append("first")
            charge("tool_calls")
            actions.append("second")
            return {}

        record = cast_candidate(
            build_kernel(execute),
            spell,
            effect_id="act",
            caster={"id": "agent-1", "kind": "agent"},
            target={"id": "one", "items": ["a"]},
        )
        self.assertEqual(["first"], actions)
        self.assertEqual("failed", record["outcome"])
        cost_observation = next(item for item in record["observations"] if item["id"] == "tool-budget")
        self.assertEqual("during", cost_observation["phase"])
        self.assertEqual("violated", cost_observation["status"])

    def test_candidate_duration_requirement_contains_execution(self):
        spell = deepcopy(self.spell)
        duration = next(item for item in spell["effects"][0]["requirements"]["during"] if "duration" in item)
        duration["duration"]["execution_max_ms"] = 10

        def execute(normalized, effect_id, context, execution_max_ms):
            context["cost"]["charge"]("tool_calls")
            subprocess.run(
                [sys.executable, "-c", "import time; time.sleep(0.1)"],
                check=True,
                timeout=execution_max_ms / 1000,
            )
            context["target"]["done"] = True
            return {}

        record = cast_candidate(
            build_kernel(execute),
            spell,
            effect_id="act",
            caster={"id": "agent-1", "kind": "agent"},
            target={"id": "one", "items": ["a"]},
        )
        self.assertEqual("failed", record["outcome"])
        duration_observation = next(item for item in record["observations"] if item["id"] == "execution-time")
        self.assertEqual("during", duration_observation["phase"])
        self.assertEqual("violated", duration_observation["status"])
        self.assertTrue(any(item["id"] == "effect-confirmed" for item in record["observations"]))

    def test_candidate_authority_requirement_refuses(self):
        calls = []

        def execute(spell, effect_id, context, execution_max_ms):
            calls.append("executed")
            return {}

        record = cast_candidate(
            build_kernel(execute, authorized=False),
            self.spell,
            effect_id="act",
            caster={"id": "agent-1", "kind": "agent"},
            target={"id": "one", "items": ["a"]},
        )
        self.assertEqual([], calls)
        self.assertEqual("refused", record["closure"]["decision"])
        authority = next(item for item in record["observations"] if item["id"] == "write-authority")
        self.assertEqual("denied", authority["status"])


if __name__ == "__main__":
    unittest.main()
