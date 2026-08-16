"""Requirements compile into typed Runtime Obligations (issue #32).

#13 moved Requirement matching from operation strings to typed demands against
concrete capability receipts. Routing *every* Requirement through that matcher
would recreate the same architectural error one layer up: a capability proves a
mechanism exists with sufficient capacity, and cannot prove a temporal property,
a whole-runtime law, or that an implementation realizes its intended Effect.
"""

from __future__ import annotations

import unittest

from environment.magic import MagicLimits, MagicRuntime
from practitioner import (
    CAPABILITY_GATE,
    DISCHARGED,
    GLOBAL_INVARIANT,
    NOT_APPLICABLE,
    PROVENANCE_PROOF,
    SEMANTIC_TRIAL,
    STATE_PREDICATE,
    TEMPORAL_MONITOR,
    UNRESOLVED,
    VIOLATED,
    CapabilityReceipt,
    Demand,
    DischargeMechanism,
    ObligationError,
    RuntimeObligation,
    Situation,
    compile_obligation_plan,
    discharge,
)


def receipt(name="familiar persistence", operations=("write",), capacity=None):
    return CapabilityReceipt(
        name=name,
        environment="local",
        operations=tuple(operations),
        status="available",
        authority="bdo",
        locator="familiar-store",
        evidence="probe:ok",
        capacity=capacity or {},
    )


def situation(*receipts):
    return Situation(
        "situation-1", "session-1", {"id": "bdo", "kind": "human"}, {"caster": "bdo"},
        ("local",), tuple(receipts), (),
    )


def outcomes_by_id(results):
    return {item.obligation_id: item for item in results}


# -- mechanisms -----------------------------------------------------------


def state_predicate_mechanism(mechanism_id="fs-probe", provenance="environment.filesystem"):
    def check(obligation, context):
        key = obligation.spec["key"]
        expected = obligation.spec["equals"]
        actual = context.get("state", {}).get(key)
        return actual == expected, {"key": key, "expected": expected, "actual": actual}

    return DischargeMechanism(
        id=mechanism_id, kind=STATE_PREDICATE, provenance=provenance,
        evidence_contract="observed-state-snapshot", check=check,
    )


def temporal_monitor_mechanism():
    """Checks a ceiling over every step of an ordered trace."""

    def check(obligation, context):
        ceiling = obligation.spec["ceiling"]
        trace = context.get("trace", ())
        breaches = [(index, value) for index, value in enumerate(trace) if value > ceiling]
        return not breaches, {"ceiling": ceiling, "steps": len(trace), "breaches": breaches}

    return DischargeMechanism(
        id="trace-monitor", kind=TEMPORAL_MONITOR, provenance="environment.execution-trace",
        evidence_contract="ordered-step-trace", check=check,
    )


def conservation_mechanism():
    """Reads whole-runtime Mana state. No Technique capability participates."""

    def check(obligation, context):
        magic = context["magic"]
        expected = obligation.spec["total"]
        actual = magic.total()
        return actual == expected, {"expected": expected, "actual": actual}

    return DischargeMechanism(
        id="mana-conservation", kind=GLOBAL_INVARIANT, provenance="environment.magic-runtime",
        evidence_contract="whole-runtime-accounting", check=check,
    )


def magic_runtime():
    return MagicRuntime(
        10,
        MagicLimits(max_network=6, max_local=5, max_personal=3, max_cast=2,
                    max_committed=4, max_restored=1, max_level=3, drain_rate=1),
        access_resolver=lambda actor, operation, locality: True,
        route_resolver=lambda source, target: True,
    )


class BrokenAccounting:
    """A stand-in whose books do not balance, so the invariant has something to catch."""

    def total(self):
        return 9


# -- shape ----------------------------------------------------------------


class ObligationShapeTests(unittest.TestCase):
    def test_only_a_capability_gate_carries_a_demand(self):
        with self.assertRaisesRegex(ObligationError, "not a capability lookup"):
            RuntimeObligation(
                id="o1", requirement_id="r1", kind=GLOBAL_INVARIANT, phase="after",
                demand=Demand(operation="write"),
            )

    def test_a_capability_gate_without_a_demand_is_refused(self):
        with self.assertRaisesRegex(ObligationError, "requires a demand"):
            RuntimeObligation(id="o1", requirement_id="r1", kind=CAPABILITY_GATE, phase="before")

    def test_unknown_kinds_and_phases_are_refused(self):
        with self.assertRaisesRegex(ObligationError, "unknown obligation kind"):
            RuntimeObligation(id="o1", requirement_id="r1", kind="vibes", phase="before")
        with self.assertRaisesRegex(ObligationError, "unknown obligation phase"):
            RuntimeObligation(id="o1", requirement_id="r1", kind=STATE_PREDICATE, phase="whenever")

    def test_a_capability_gate_cannot_be_registered_as_a_checker(self):
        with self.assertRaisesRegex(ObligationError, "not by a registered checker"):
            DischargeMechanism(
                id="m", kind=CAPABILITY_GATE, provenance="p",
                evidence_contract="c", check=lambda o, c: True,
            )


class OneRequirementManyObligationsTests(unittest.TestCase):
    """Scope compiles to a capability gate *and* a downstream observation."""

    def test_a_requirement_compiles_to_a_capability_gate_and_a_non_capability_obligation(self):
        obligations = [
            RuntimeObligation(
                id="scope.gate", requirement_id="bounded-scope", kind=CAPABILITY_GATE,
                phase="before",
                demand=Demand(operation="mutate", relation="scope",
                              capacity={"admissible": ("a.txt",)}, attenuate=True),
            ),
            RuntimeObligation(
                id="scope.residual", requirement_id="bounded-scope", kind=STATE_PREDICATE,
                phase="after", spec={"key": "outside", "equals": "untouched"},
            ),
        ]
        plan = compile_obligation_plan(
            obligations,
            situation(receipt("fs view", ("mutate",), {"region": ("a.txt",)})),
            [state_predicate_mechanism()],
        )
        self.assertTrue(plan.ready)

        results = outcomes_by_id(discharge(plan, {"state": {"outside": "untouched"}}))
        self.assertEqual(DISCHARGED, results["scope.gate"].status)
        self.assertEqual(DISCHARGED, results["scope.residual"].status)
        # Same Requirement, two evidence classes, two mechanisms.
        self.assertEqual("bounded-scope", results["scope.gate"].requirement_id)
        self.assertEqual("bounded-scope", results["scope.residual"].requirement_id)
        self.assertNotEqual(results["scope.gate"].kind, results["scope.residual"].kind)

    def test_only_capability_gates_reach_the_capability_matcher(self):
        obligations = [
            RuntimeObligation(id="gate", requirement_id="r", kind=CAPABILITY_GATE,
                              phase="before", demand=Demand(operation="write")),
            RuntimeObligation(id="pred", requirement_id="r", kind=STATE_PREDICATE,
                              phase="after", spec={"key": "k", "equals": 1}),
            RuntimeObligation(id="law", requirement_id="r", kind=GLOBAL_INVARIANT,
                              phase="after", spec={"total": 10}),
        ]
        plan = compile_obligation_plan(
            obligations, situation(receipt()),
            [state_predicate_mechanism(), conservation_mechanism()],
        )
        self.assertEqual(["gate"], list(plan.capability_plan.matches))
        self.assertNotIn("pred", plan.capability_plan.matches)
        self.assertNotIn("law", plan.capability_plan.matches)


class TemporalObligationTests(unittest.TestCase):
    def test_a_temporal_property_survives_a_trace_that_a_snapshot_cannot_see(self):
        """Pre and post are identical and legal. The middle is not."""
        obligations = [
            RuntimeObligation(id="ceiling.snapshot", requirement_id="bounded-depth",
                              kind=STATE_PREDICATE, phase="after",
                              spec={"key": "depth", "equals": 0}),
            RuntimeObligation(id="ceiling.trace", requirement_id="bounded-depth",
                              kind=TEMPORAL_MONITOR, phase="after", spec={"ceiling": 3}),
        ]
        plan = compile_obligation_plan(
            obligations, situation(receipt()),
            [state_predicate_mechanism(), temporal_monitor_mechanism()],
        )

        context = {"state": {"depth": 0}, "trace": (0, 2, 5, 2, 0)}
        results = outcomes_by_id(discharge(plan, context))

        # The snapshot is satisfied: before and after both read 0.
        self.assertEqual(DISCHARGED, results["ceiling.snapshot"].status)
        # The trace is not. This is the case a pre/post pair cannot represent.
        self.assertEqual(VIOLATED, results["ceiling.trace"].status)
        self.assertEqual([(2, 5)], results["ceiling.trace"].detail["breaches"])

    def test_a_trace_that_never_breaches_discharges(self):
        obligations = [RuntimeObligation(id="t", requirement_id="r", kind=TEMPORAL_MONITOR,
                                         phase="after", spec={"ceiling": 3})]
        plan = compile_obligation_plan(obligations, situation(), [temporal_monitor_mechanism()])
        results = outcomes_by_id(discharge(plan, {"trace": (0, 1, 3, 1, 0)}))
        self.assertEqual(DISCHARGED, results["t"].status)


class GlobalInvariantTests(unittest.TestCase):
    def test_conservation_is_checked_without_any_technique_capability(self):
        obligations = [RuntimeObligation(id="mana.total", requirement_id="conservation",
                                         kind=GLOBAL_INVARIANT, phase="after",
                                         spec={"total": 10})]
        # No receipts at all. A whole-runtime law is owned by no Technique.
        plan = compile_obligation_plan(obligations, situation(), [conservation_mechanism()])
        self.assertTrue(plan.ready)
        self.assertEqual({}, plan.capability_plan.matches)

        magic = magic_runtime()
        magic.claim("bdo", "network", 2)
        results = outcomes_by_id(discharge(plan, {"magic": magic}))

        self.assertEqual(DISCHARGED, results["mana.total"].status)
        self.assertEqual(10, results["mana.total"].detail["actual"])
        self.assertEqual("environment.magic-runtime", results["mana.total"].provenance)

    def test_the_invariant_catches_state_that_does_not_account_for_the_total(self):
        obligations = [RuntimeObligation(id="mana.total", requirement_id="conservation",
                                         kind=GLOBAL_INVARIANT, phase="after",
                                         spec={"total": 10})]
        plan = compile_obligation_plan(obligations, situation(), [conservation_mechanism()])
        results = outcomes_by_id(discharge(plan, {"magic": BrokenAccounting()}))

        self.assertEqual(VIOLATED, results["mana.total"].status)
        self.assertEqual({"expected": 10, "actual": 9},
                         {k: results["mana.total"].detail[k] for k in ("expected", "actual")})


class FailClosedTests(unittest.TestCase):
    def test_a_required_pre_closure_obligation_with_no_mechanism_is_a_gap(self):
        obligations = [RuntimeObligation(id="pred", requirement_id="r", kind=STATE_PREDICATE,
                                         phase="before", spec={"key": "k", "equals": 1})]
        plan = compile_obligation_plan(obligations, situation(), [])
        self.assertFalse(plan.ready)
        self.assertEqual(("obligation-undischargeable:pred:state_predicate",), plan.gaps)

    def test_a_required_capability_gate_with_no_receipt_is_a_gap(self):
        obligations = [RuntimeObligation(id="gate", requirement_id="r", kind=CAPABILITY_GATE,
                                         phase="before", demand=Demand(operation="write"))]
        plan = compile_obligation_plan(obligations, situation(), [])
        self.assertFalse(plan.ready)
        self.assertIn("obligation-undischargeable:gate:capability_gate", plan.gaps)

    def test_an_after_phase_obligation_without_a_mechanism_is_unresolved_not_a_gap(self):
        """Closure is not blocked by evidence that cannot exist until after execution."""
        obligations = [RuntimeObligation(id="trial", requirement_id="r", kind=SEMANTIC_TRIAL,
                                         phase="after", spec={})]
        plan = compile_obligation_plan(obligations, situation(), [])
        self.assertTrue(plan.ready)
        results = outcomes_by_id(discharge(plan, {}))
        self.assertEqual(UNRESOLVED, results["trial"].status)

    def test_an_optional_obligation_without_a_mechanism_is_not_applicable(self):
        obligations = [RuntimeObligation(id="opt", requirement_id="r", kind=PROVENANCE_PROOF,
                                         phase="before", required=False, spec={})]
        plan = compile_obligation_plan(obligations, situation(), [])
        self.assertTrue(plan.ready)
        results = outcomes_by_id(discharge(plan, {}))
        self.assertEqual(NOT_APPLICABLE, results["opt"].status)

    def test_two_mechanisms_of_the_same_kind_fail_closed_as_ambiguous(self):
        obligations = [RuntimeObligation(id="pred", requirement_id="r", kind=STATE_PREDICATE,
                                         phase="before", spec={"key": "k", "equals": 1})]
        plan = compile_obligation_plan(
            obligations, situation(),
            [state_predicate_mechanism("probe-a"), state_predicate_mechanism("probe-b")],
        )
        self.assertFalse(plan.ready)
        self.assertEqual(("obligation-ambiguous:pred:probe-a,probe-b",), plan.gaps)

    def test_a_checker_that_raises_is_unresolved_rather_than_satisfied(self):
        def explode(obligation, context):
            raise RuntimeError("prover crashed")

        mechanism = DischargeMechanism(id="prover", kind=STATE_PREDICATE,
                                       provenance="external.prover",
                                       evidence_contract="proof-object", check=explode)
        obligations = [RuntimeObligation(id="pred", requirement_id="r", kind=STATE_PREDICATE,
                                         phase="after", spec={})]
        plan = compile_obligation_plan(obligations, situation(), [mechanism])
        results = outcomes_by_id(discharge(plan, {}))

        self.assertEqual(UNRESOLVED, results["pred"].status)
        self.assertIn("prover crashed", results["pred"].detail["error"])
        self.assertEqual("external.prover", results["pred"].provenance)

    def test_duplicate_obligation_ids_are_refused(self):
        obligation = RuntimeObligation(id="dup", requirement_id="r", kind=STATE_PREDICATE,
                                       phase="after", spec={})
        with self.assertRaisesRegex(ObligationError, "duplicate obligation id"):
            compile_obligation_plan([obligation, obligation], situation(), [])


class EvidenceNotAuthorityTests(unittest.TestCase):
    def test_every_outcome_retains_the_provenance_of_what_produced_it(self):
        obligations = [
            RuntimeObligation(id="gate", requirement_id="r", kind=CAPABILITY_GATE,
                              phase="before", demand=Demand(operation="write")),
            RuntimeObligation(id="pred", requirement_id="r", kind=STATE_PREDICATE,
                              phase="after", spec={"key": "k", "equals": 1}),
        ]
        plan = compile_obligation_plan(obligations, situation(receipt()),
                                       [state_predicate_mechanism()])
        results = outcomes_by_id(discharge(plan, {"state": {"k": 1}}))

        self.assertEqual("probe:ok", results["gate"].provenance)
        self.assertEqual("environment.filesystem", results["pred"].provenance)
        self.assertEqual("observed-state-snapshot", results["pred"].detail["evidence_contract"])

    def test_a_candidate_cannot_supply_the_trial_that_promotes_itself(self):
        obligations = [RuntimeObligation(id="trial", requirement_id="r", kind=SEMANTIC_TRIAL,
                                         phase="before", spec={"subject": "generated.technique.v1"})]
        self_evaluator = DischargeMechanism(
            id="self-test", kind=SEMANTIC_TRIAL, provenance="generated.technique.v1",
            evidence_contract="self-generated-suite", check=lambda o, c: True,
        )
        plan = compile_obligation_plan(obligations, situation(), [self_evaluator])
        self.assertFalse(plan.ready)
        self.assertEqual(("obligation-undischargeable:trial:semantic_trial",), plan.gaps)

    def test_an_independent_evaluator_discharges_the_same_trial(self):
        obligations = [RuntimeObligation(id="trial", requirement_id="r", kind=SEMANTIC_TRIAL,
                                         phase="before", spec={"subject": "generated.technique.v1"})]
        independent = DischargeMechanism(
            id="held-out", kind=SEMANTIC_TRIAL, provenance="evaluator.held-out-suite",
            evidence_contract="independent-discriminating-trials", check=lambda o, c: True,
        )
        plan = compile_obligation_plan(obligations, situation(), [independent])
        self.assertTrue(plan.ready)
        results = outcomes_by_id(discharge(plan, {}))
        self.assertEqual(DISCHARGED, results["trial"].status)
        self.assertEqual("evaluator.held-out-suite", results["trial"].provenance)


class PhaseFilterTests(unittest.TestCase):
    def test_discharge_can_be_restricted_to_one_phase(self):
        obligations = [
            RuntimeObligation(id="early", requirement_id="r", kind=STATE_PREDICATE,
                              phase="before", spec={"key": "k", "equals": 1}),
            RuntimeObligation(id="late", requirement_id="r", kind=TEMPORAL_MONITOR,
                              phase="after", spec={"ceiling": 3}),
        ]
        plan = compile_obligation_plan(
            obligations, situation(),
            [state_predicate_mechanism(), temporal_monitor_mechanism()],
        )
        early = discharge(plan, {"state": {"k": 1}}, phase="before")
        self.assertEqual(["early"], [item.obligation_id for item in early])


if __name__ == "__main__":
    unittest.main()
