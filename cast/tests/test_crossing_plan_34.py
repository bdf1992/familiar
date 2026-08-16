"""CrossingPlan, Brink, and Closure (issue #34).

0.7's claim is that an effectful Cast executes under exactly the bindings and
obligations that were authorized. That claim is defeated if the plan can change
between Closure and execution without the runtime refusing or recording it.

These tests are adversarial where it matters. The happy path is one test; the
rest try to move something after Closure and check that it is caught and named.
"""

from __future__ import annotations

import unittest

from practitioner import (
    CAPABILITY_GATE,
    STATE_PREDICATE,
    CapabilityReceipt,
    Demand,
    DischargeMechanism,
    RuntimeObligation,
    Situation,
    compile_obligation_plan,
)
from practitioner.crossing import (
    BrinkFinding,
    CrossingPlan,
    CrossingPlanError,
    EvidenceContract,
    ManaParticipation,
    ResidualBounds,
    canonical_material,
    close,
    digest_matches,
    observe_brink,
    plan_digest,
    verify,
)

CONFIGURATION = {
    "spell": "workspace-tidy",
    "version": "0.1.0",
    "effect": "tidy",
    "caster": "bdo",
    "target": "workspace/a",
    "technique": "scripts/tidy.py",
}


def receipt(name="workspace write", operations=("write",), capacity=None, authority="bdo"):
    return CapabilityReceipt(
        name=name,
        environment="local",
        operations=tuple(operations),
        status="available",
        authority=authority,
        locator="workspace",
        evidence="probe:ok",
        capacity=capacity or {"permissions": ["write"]},
    )


def situation(*receipts):
    return Situation(
        "situation-1", "session-1", {"id": "bdo", "kind": "human"}, {"caster": "bdo"},
        ("local",), tuple(receipts), (),
    )


def obligation_plan(*, receipts=None, spec=None, demand=None):
    """A two-obligation plan: one capability gate, one state predicate."""
    gate = RuntimeObligation(
        id="write-gate",
        requirement_id="write-authority",
        kind=CAPABILITY_GATE,
        phase="before",
        demand=demand or Demand(operation="write", relation="permissions",
                                capacity={"permissions": ["write"]}),
    )
    predicate = RuntimeObligation(
        id="target-clean",
        requirement_id="target-observable",
        kind=STATE_PREDICATE,
        phase="after",
        spec=spec or {"expect": "clean"},
    )
    mechanism = DischargeMechanism(
        id="fs-predicate",
        kind=STATE_PREDICATE,
        provenance="environment.local",
        evidence_contract="filesystem-observation",
        check=lambda obligation, context: True,
    )
    return compile_obligation_plan(
        (gate, predicate),
        situation(*(receipts or (receipt(),))),
        (mechanism,),
    )


def crossing_plan(**overrides):
    base = dict(
        configuration=dict(CONFIGURATION),
        obligations=obligation_plan(),
        mana=(ManaParticipation(locality="local", participant="bdo", claim=10, commit=6),),
        evidence_contracts=(
            EvidenceContract(
                obligation_id="target-clean",
                contract="filesystem-observation",
                observer="environment.local",
            ),
        ),
        residual_bounds=ResidualBounds(("advisory",)),
    )
    base.update(overrides)
    return CrossingPlan(**base)


def at_brink():
    return BrinkFinding(effect_delta=0, mana_delta=0)


class ClosureTests(unittest.TestCase):
    def test_a_complete_plan_closes_and_takes_an_identity(self):
        plan = crossing_plan()
        self.assertTrue(plan.ready, plan.gaps)
        closed = close(plan, at_brink())
        self.assertTrue(closed.digest.startswith("sha256:"))
        self.assertEqual(closed.digest, plan_digest(plan))

    def test_closure_refuses_when_an_obligation_has_no_discharge_path(self):
        """A plan with a gap describes something other than what will happen.

        `before`, because #32 fails closed on a required before-or-during
        obligation with no viable path. An unbindable `after` obligation is not
        a closure gap -- it is an unresolved status later, which is a different
        thing and is #35's to report.
        """
        plan = crossing_plan(obligations=compile_obligation_plan(
            (RuntimeObligation(
                id="unbindable",
                requirement_id="r",
                kind=STATE_PREDICATE,
                phase="before",
            ),),
            situation(receipt()),
            (),
        ))
        self.assertFalse(plan.ready)
        with self.assertRaises(CrossingPlanError) as caught:
            close(plan, at_brink())
        self.assertIn("closure-gap", str(caught.exception))

    def test_closure_refuses_when_the_cast_has_already_had_an_effect(self):
        with self.assertRaises(CrossingPlanError) as caught:
            close(crossing_plan(), BrinkFinding(effect_delta=1, mana_delta=0))
        self.assertIn("brink-effect-already-applied", str(caught.exception))

    def test_closure_refuses_when_mana_is_already_committed(self):
        """A pre-Closure refusal must leave no Cast-attributable commitment."""
        with self.assertRaises(CrossingPlanError) as caught:
            close(crossing_plan(), BrinkFinding(effect_delta=0, mana_delta=4))
        self.assertIn("brink-mana-already-committed", str(caught.exception))

    def test_an_unobserved_brink_does_not_close(self):
        """Nobody looking is not the same as nothing having happened."""
        finding = observe_brink(None, None)
        self.assertFalse(finding.at_brink)
        with self.assertRaises(CrossingPlanError) as caught:
            close(crossing_plan(), finding)
        self.assertIn("brink-unobservable", str(caught.exception))

    def test_a_probe_that_raises_is_unobservable_not_zero(self):
        def broken():
            raise RuntimeError("ledger unavailable")

        finding = observe_brink(lambda: 0, broken)
        self.assertFalse(finding.at_brink)
        self.assertTrue(any("ledger unavailable" in item for item in finding.unobservable))

    def test_a_clean_pair_of_probes_reaches_the_brink(self):
        finding = observe_brink(lambda: 0, lambda: 0)
        self.assertTrue(finding.at_brink)
        self.assertEqual((), finding.reasons())

    def test_other_activity_does_not_prevent_the_brink(self):
        """Only Cast-attributable deltas matter; a busy runtime is still closable."""
        finding = observe_brink(lambda: 0, lambda: 0)
        self.assertTrue(finding.at_brink)


class PlanIdentityTests(unittest.TestCase):
    def test_canonically_equivalent_plans_have_the_same_digest(self):
        """Key order and mapping identity are not material."""
        reordered = dict(reversed(list(CONFIGURATION.items())))
        self.assertNotEqual(list(CONFIGURATION), list(reordered))
        self.assertEqual(
            plan_digest(crossing_plan()),
            plan_digest(crossing_plan(configuration=reordered)),
        )

    def test_a_material_change_changes_the_digest(self):
        other = dict(CONFIGURATION, target="workspace/b")
        self.assertNotEqual(
            plan_digest(crossing_plan()),
            plan_digest(crossing_plan(configuration=other)),
        )

    def test_the_sealed_material_is_readable_without_a_hash(self):
        material = canonical_material(crossing_plan())
        self.assertEqual("0.7-draft", material["crossing_plan_version"])
        for key in ("configuration", "capacity", "obligations", "mana",
                    "evidence_contracts", "residual_bounds"):
            self.assertIn(key, material)

    def test_the_three_algebras_stay_separate_in_the_sealed_material(self):
        """Coupling is not merging. #47 refused the collapse; this preserves it."""
        material = canonical_material(crossing_plan())
        self.assertIn("write-gate", material["obligations"])
        self.assertIn("write-gate", material["capacity"])
        self.assertEqual(
            [{"locality": "local", "participant": "bdo", "claim": 10, "commit": 6}],
            material["mana"],
        )
        # An obligation carries no Mana cost and Mana carries no capability demand.
        self.assertNotIn("mana", material["obligations"]["write-gate"])
        self.assertNotIn("demand", material["mana"][0])


class PostClosureMutationTests(unittest.TestCase):
    """#34's defeating case: executing under materially different bindings."""

    def setUp(self):
        self.closed = close(crossing_plan(), at_brink())

    def assert_caught(self, observed, path_fragment):
        self.assertFalse(digest_matches(self.closed, observed))
        violations = verify(self.closed, observed)
        self.assertNotEqual((), violations)
        self.assertTrue(
            any(path_fragment in violation.path for violation in violations),
            f"no violation named {path_fragment}: {[v.path for v in violations]}",
        )
        return violations

    def test_a_swapped_target_is_caught_and_named(self):
        observed = crossing_plan(configuration=dict(CONFIGURATION, target="workspace/elsewhere"))
        violations = self.assert_caught(observed, "configuration.target")
        violation = next(v for v in violations if v.path == "configuration.target")
        self.assertEqual("workspace/a", violation.closed)
        self.assertEqual("workspace/elsewhere", violation.observed)

    def test_a_swapped_technique_is_caught(self):
        self.assert_caught(
            crossing_plan(configuration=dict(CONFIGURATION, technique="scripts/other.py")),
            "configuration.technique",
        )

    def test_a_swapped_capability_binding_is_caught(self):
        """A different receipt behind the same requirement id."""
        self.assert_caught(
            crossing_plan(obligations=obligation_plan(
                receipts=(receipt(name="wider workspace write"),),
            )),
            "capacity.write-gate",
        )

    def test_a_widened_authority_is_caught(self):
        self.assert_caught(
            crossing_plan(obligations=obligation_plan(
                receipts=(receipt(authority="root"),),
            )),
            "capacity.write-gate",
        )

    def test_a_widened_scope_on_the_handle_is_caught(self):
        """Attenuation lives only in capacity; sealing it is what catches this."""
        self.assert_caught(
            crossing_plan(obligations=obligation_plan(
                receipts=(receipt(capacity={"permissions": ["write", "delete"]}),),
            )),
            "capacity.write-gate",
        )

    def test_a_changed_obligation_contract_is_caught(self):
        self.assert_caught(
            crossing_plan(obligations=obligation_plan(spec={"expect": "anything"})),
            "obligations.target-clean",
        )

    def test_a_changed_evidence_contract_is_caught(self):
        self.assert_caught(
            crossing_plan(evidence_contracts=(
                EvidenceContract(
                    obligation_id="target-clean",
                    contract="the-executor-says-so",
                    observer="scripts/tidy.py",
                ),
            )),
            "evidence_contracts",
        )

    def test_widened_residual_bounds_are_caught(self):
        self.assert_caught(
            crossing_plan(residual_bounds=ResidualBounds(("advisory", "data-loss"))),
            "residual_bounds",
        )

    def test_an_increased_mana_commitment_is_caught(self):
        self.assert_caught(
            crossing_plan(mana=(
                ManaParticipation(locality="local", participant="bdo", claim=10, commit=10),
            )),
            "mana",
        )

    def test_every_difference_is_reported_not_just_the_first(self):
        """A record saying only 'the plan changed' cannot be acted on."""
        observed = crossing_plan(
            configuration=dict(CONFIGURATION, target="elsewhere", technique="other.py"),
        )
        paths = {violation.path for violation in verify(self.closed, observed)}
        self.assertIn("configuration.target", paths)
        self.assertIn("configuration.technique", paths)

    def test_an_unchanged_plan_produces_no_violations(self):
        self.assertTrue(digest_matches(self.closed, crossing_plan()))
        self.assertEqual((), verify(self.closed, crossing_plan()))


class WhatMayStillMoveTests(unittest.TestCase):
    """Closure freezes the plan, not the record. The distinction is the point."""

    def test_the_closed_plan_carries_no_findings_or_outcome(self):
        closed = close(crossing_plan(), at_brink())
        material = closed.material()
        for evolving in ("outcome", "findings", "status", "settlement", "residuals"):
            self.assertNotIn(evolving, material)

    def test_runtime_evidence_does_not_change_the_plan_identity(self):
        """Evidence appearing after Closure must not be able to reseal the plan."""
        plan = crossing_plan()
        closed = close(plan, at_brink())
        before = closed.digest
        # Whatever a later phase learns, it learns about this same plan.
        self.assertEqual(before, plan_digest(plan))
        self.assertEqual(before, closed.digest)

    def test_a_residual_outside_the_bound_is_detectable_after_closure(self):
        closed = close(crossing_plan(), at_brink())
        exceeded = closed.plan.residual_bounds.exceeded_by(("advisory", "data-loss"))
        self.assertEqual(("data-loss",), exceeded)

    def test_a_residual_inside_the_bound_is_not_a_breach(self):
        closed = close(crossing_plan(), at_brink())
        self.assertEqual((), closed.plan.residual_bounds.exceeded_by(("advisory",)))


class PlanConstructionTests(unittest.TestCase):
    def test_a_plan_intending_to_commit_more_mana_than_it_claims_is_refused(self):
        with self.assertRaises(CrossingPlanError):
            ManaParticipation(locality="local", participant="bdo", claim=2, commit=3)

    def test_two_evidence_contracts_for_one_obligation_are_refused(self):
        """One obligation has one standard, fixed before anything runs."""
        with self.assertRaises(CrossingPlanError):
            crossing_plan(evidence_contracts=(
                EvidenceContract("target-clean", "a", "environment.local"),
                EvidenceContract("target-clean", "b", "environment.local"),
            ))

    def test_a_plan_without_a_resolved_configuration_is_refused(self):
        with self.assertRaises(CrossingPlanError):
            crossing_plan(configuration={})

    def test_empty_residual_bounds_must_be_written_not_defaulted(self):
        """Tolerating nothing is a strong claim, so it is never implicit."""
        plan = CrossingPlan(configuration=dict(CONFIGURATION), obligations=obligation_plan())
        self.assertEqual((), plan.residual_bounds.permitted)
        self.assertEqual(("advisory",), plan.residual_bounds.exceeded_by(("advisory",)))


if __name__ == "__main__":
    unittest.main()
