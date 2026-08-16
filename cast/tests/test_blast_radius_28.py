"""Ambient reactive blast radius beyond direct capabilities (issue #28).

Effect-path attenuation can correctly constrain what a Technique reaches
directly while the Environment still contains machinery outside that handle
hierarchy. A scoped file mutation may trigger watchers, CI, webhooks or
deployments the Technique never invoked. Direct Scope enforcement is necessary
and is not sufficient.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
import unittest

from environment.blast_radius import (
    BlastRadiusError,
    DownstreamObservation,
    ReactiveEdge,
    ReactiveGraph,
    characterize,
)
from environment.authority import RecordingHostCredential, attenuated_credential_enforcer
from environment.scope import mapping_scope_enforcer
from kernel.spell_kernel import SpellKernel
from validation.candidate_adapter import load_candidate_spell
from validation.casting_04 import cast_with_binding

ROOT = Path(__file__).resolve().parents[1]
SPELL = ROOT / "validation" / "candidate" / "SPELL.md"
ADMISSIBLE_KEYS = ("id", "items", "done", "valid")


class Watcher:
    """A stand-in reactive mechanism. Nothing invokes it; it reacts."""

    def __init__(self, watching: str, writes: str):
        self.watching = watching
        self.writes = writes
        self.fired: list[str] = []

    def react(self, mutated: list[str]) -> list[DownstreamObservation]:
        if self.watching not in mutated:
            return []
        self.fired.append(self.writes)
        return [
            DownstreamObservation(
                mechanism=f"watcher:{self.watching}", target=self.writes,
                observer="environment.watcher-probe", detail={"triggered_by": self.watching},
            )
        ]


def target_observable(phase, context):
    target = context.get("target")
    return isinstance(target, Mapping) and isinstance(target.get("items"), list)


def effect_confirmed(phase, context):
    return (context.get("target") or {}).get("done") is True


def execute(spell, effect_id, context, execution_max_ms):
    context["cost"]["charge"]("tool_calls")
    context["target"]["done"] = True
    return {}


def binding():
    return {
        "binding_format": "0.4-draft",
        "id": "reactive-technique",
        "version": "1.0.0",
        "kind": "service",
        "realizes": {"spell": "bounded-work", "spell_version": "0.0.0", "effect": "act"},
        "mechanisms": {
            "authority": True, "scope": ["max_items"],
            "cost": ["tool_calls"], "duration": ["execution_max_ms"],
        },
    }


def make_kernel(observer=None):
    return SpellKernel(
        requirements={"target-observable": target_observable, "effect-confirmed": effect_confirmed},
        authority_resolver=lambda caster, permission, context: permission == "workspace.write",
        scope_resolver=lambda target, context: list(target["items"]),
        scope_enforcer=mapping_scope_enforcer(ADMISSIBLE_KEYS),
        authority_enforcer=attenuated_credential_enforcer(RecordingHostCredential()),
        blast_radius_observer=observer,
        executor=execute,
    )


def run(kernel, spell, **kwargs):
    return cast_with_binding(
        kernel, spell, binding(), effect_id="act",
        caster={"id": "agent-1", "kind": "agent"},
        target={"id": "one", "items": ["a.txt"], "done": False},
        **kwargs,
    )


def containment_observation(record):
    return next(
        item for item in record["observations"]
        if item["id"] == "downstream-containment" and item["phase"] == "after"
    )


class ReachDistinctionTests(unittest.TestCase):
    """direct != declared != observed != unknown."""

    def test_no_graph_means_unknown_not_empty(self):
        radius = characterize(["a.txt"], None)
        self.assertTrue(radius.unknown)
        self.assertEqual((), radius.declared)
        self.assertFalse(radius.contained)
        self.assertIn("no reactive dependency graph", radius.unknown_reason)

    def test_an_incomplete_graph_still_reports_unknown(self):
        graph = ReactiveGraph([ReactiveEdge("a.txt", "build/out", "watcher")], complete=False)
        radius = characterize(["a.txt"], graph)

        self.assertEqual(1, len(radius.declared))
        self.assertTrue(radius.unknown)
        self.assertFalse(radius.contained)

    def test_a_complete_graph_with_no_escape_is_contained(self):
        graph = ReactiveGraph([], complete=True)
        radius = characterize(["a.txt"], graph)

        self.assertFalse(radius.unknown)
        self.assertTrue(radius.contained)

    def test_observing_nothing_is_not_the_same_as_containment(self):
        """The distinction the whole issue turns on."""
        incomplete = characterize(["a.txt"], ReactiveGraph([], complete=False))
        complete = characterize(["a.txt"], ReactiveGraph([], complete=True))

        self.assertEqual((), incomplete.escaped_direct)
        self.assertEqual((), complete.escaped_direct)
        # Same observations. Only one of them established containment.
        self.assertFalse(incomplete.contained)
        self.assertTrue(complete.contained)

    def test_declared_reach_is_transitive(self):
        graph = ReactiveGraph(
            [
                ReactiveEdge("a.txt", "build/out", "watcher"),
                ReactiveEdge("build/out", "deploy", "ci"),
                ReactiveEdge("unrelated", "elsewhere", "other"),
            ],
            complete=True,
        )
        reached = {edge.target for edge in graph.downstream(["a.txt"])}
        self.assertEqual({"build/out", "deploy"}, reached)

    def test_a_malformed_edge_or_observation_is_refused(self):
        with self.assertRaisesRegex(BlastRadiusError, "requires mechanism"):
            ReactiveEdge("a", "b", "")
        with self.assertRaisesRegex(BlastRadiusError, "requires observer"):
            DownstreamObservation("watcher", "b", "")


class WatcherFixtureTests(unittest.TestCase):
    """An in-Scope mutation triggers an out-of-Scope downstream mutation."""

    def setUp(self):
        self.spell = load_candidate_spell(SPELL)

    def test_an_in_scope_mutation_reaches_outside_through_a_watcher(self):
        watcher = Watcher(watching="a.txt", writes="build/artifact")
        graph = ReactiveGraph([ReactiveEdge("a.txt", "build/artifact", "watcher:a.txt")],
                              complete=True)

        def observer(spell, effect_id, context, scope_boundary):
            return characterize(["a.txt"], graph, watcher.react(["a.txt"]))

        record = run(make_kernel(observer), self.spell)

        # The direct path was contained: Scope enforcement is untouched.
        scope = next(
            item for item in record["observations"]
            if item["id"] == "bounded-scope" and item["phase"] == "after"
        )
        self.assertEqual("satisfied", scope["status"])

        # And something still escaped.
        containment = containment_observation(record)
        self.assertEqual("violated", containment["status"])
        self.assertEqual(["build/artifact"], [item["target"] for item in containment["value"]["escaped_direct"]])
        self.assertEqual(["build/artifact"], watcher.fired)
        self.assertTrue(
            any("downstream consequences outside direct reach" in item for item in record["residuals"])
        )

    def test_cast_records_the_direct_boundary_and_the_downstream_reach_separately(self):
        watcher = Watcher(watching="a.txt", writes="build/artifact")
        graph = ReactiveGraph([ReactiveEdge("a.txt", "build/artifact", "watcher:a.txt")],
                              complete=True)

        def observer(spell, effect_id, context, scope_boundary):
            return characterize(["a.txt"], graph, watcher.react(["a.txt"]))

        record = run(make_kernel(observer), self.spell)

        scope_before = next(
            item for item in record["observations"]
            if item["id"] == "bounded-scope" and item["phase"] == "before"
        )
        containment = containment_observation(record)

        # Two separate observations, two separate concerns.
        self.assertEqual("environment.mapping-view", scope_before["value"]["enforcement"]["mechanism"])
        self.assertEqual(["a.txt"], containment["value"]["direct"])
        self.assertEqual(1, len(containment["value"]["declared"]))
        self.assertEqual(1, len(containment["value"]["observed"]))
        self.assertEqual("environment.watcher-probe", containment["value"]["observed"][0]["observer"])

    def test_a_quiet_watcher_leaves_the_cast_resolved(self):
        watcher = Watcher(watching="somewhere-else", writes="build/artifact")
        graph = ReactiveGraph([], complete=True)

        def observer(spell, effect_id, context, scope_boundary):
            return characterize(["a.txt"], graph, watcher.react(["a.txt"]))

        record = run(make_kernel(observer), self.spell)

        self.assertEqual("resolved", record["outcome"])
        self.assertEqual("satisfied", containment_observation(record)["status"])
        self.assertEqual([], watcher.fired)

    def test_unknown_reach_is_recorded_rather_than_treated_as_absent(self):
        def observer(spell, effect_id, context, scope_boundary):
            return characterize(["a.txt"], None)

        record = run(make_kernel(observer), self.spell)

        containment = containment_observation(record)
        self.assertEqual("violated", containment["status"])
        self.assertTrue(containment["value"]["unknown"])
        self.assertEqual([], containment["value"]["escaped_direct"])
        self.assertTrue(any("downstream reach unknown" in item for item in record["residuals"]))


class ClosureAndOutcomeTests(unittest.TestCase):
    def setUp(self):
        self.spell = load_candidate_spell(SPELL)

    def test_closure_refuses_when_containment_is_required_and_unobservable(self):
        record = run(make_kernel(None), self.spell, downstream_containment_required=True)

        self.assertEqual("refused", record["closure"]["decision"])
        self.assertTrue(
            any("downstream-unobservable" in reason for reason in record["closure"]["reasons"])
        )
        self.assertIsNone(record["outcome"])

    def test_required_containment_fails_the_cast_when_something_escapes(self):
        watcher = Watcher(watching="a.txt", writes="build/artifact")
        graph = ReactiveGraph([ReactiveEdge("a.txt", "build/artifact", "w")], complete=True)

        def observer(spell, effect_id, context, scope_boundary):
            return characterize(["a.txt"], graph, watcher.react(["a.txt"]))

        record = run(make_kernel(observer), self.spell, downstream_containment_required=True)

        self.assertEqual("closed", record["closure"]["decision"])
        self.assertEqual("failed", record["outcome"])

    def test_unknown_reach_fails_a_cast_that_required_containment(self):
        """Cannot prove absent is not the same as proved absent."""
        def observer(spell, effect_id, context, scope_boundary):
            return characterize(["a.txt"], ReactiveGraph([], complete=False))

        record = run(make_kernel(observer), self.spell, downstream_containment_required=True)

        self.assertEqual("failed", record["outcome"])

    def test_observation_without_a_requirement_records_but_does_not_fail(self):
        """Blast radius is observed by default and only gates when declared."""
        def observer(spell, effect_id, context, scope_boundary):
            return characterize(["a.txt"], ReactiveGraph([], complete=False))

        record = run(make_kernel(observer), self.spell)

        self.assertEqual("resolved", record["outcome"])
        self.assertTrue(containment_observation(record)["value"]["unknown"])

    def test_this_does_not_weaken_scope_enforcement(self):
        """#10's direct attenuation still refuses a dishonest Technique."""
        def dishonest(spell, effect_id, context, execution_max_ms):
            context["cost"]["charge"]("tool_calls")
            context["target"]["outside"] = "reached"
            return {}

        kernel = SpellKernel(
            requirements={"target-observable": target_observable, "effect-confirmed": effect_confirmed},
            authority_resolver=lambda caster, permission, context: permission == "workspace.write",
            scope_resolver=lambda target, context: list(target["items"]),
            scope_enforcer=mapping_scope_enforcer(ADMISSIBLE_KEYS),
            authority_enforcer=attenuated_credential_enforcer(RecordingHostCredential()),
            blast_radius_observer=lambda s, e, c, b: characterize(["a.txt"], ReactiveGraph([], complete=True)),
            executor=dishonest,
        )
        record = run(kernel, self.spell)

        self.assertNotEqual("resolved", record["outcome"])
        after_scope = next(
            item for item in record["observations"]
            if item["id"] == "bounded-scope" and item["phase"] == "after"
        )
        self.assertEqual("violated", after_scope["status"])


if __name__ == "__main__":
    unittest.main()
