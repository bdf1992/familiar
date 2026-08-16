"""Semantic alignment evidence for autonomous Spellcraft (issue #29).

Schema validation, AST restrictions, sandbox conformance, fuzzing and unit
tests can all pass while a generated implementation satisfies its tests through
behaviour that defeats the declared Effect. Structural safety is not evidence
of Effect alignment.
"""

from __future__ import annotations

import unittest

from spell.alignment import (
    BEHAVIOURAL,
    CANDIDATE,
    HUMAN,
    INDEPENDENT,
    PROMOTED,
    REFUSED,
    SEMANTIC,
    AlignmentError,
    EffectInvariant,
    HumanAcceptance,
    PromotionPolicy,
    Trial,
    promote,
    run_trial,
)

# -- the Effect and its invariant ----------------------------------------

ORDERED = EffectInvariant(
    id="ordered-permutation",
    description="the result is a permutation of the input, in non-decreasing order",
    check=lambda case, result: (
        sorted(case) == sorted(result) and all(a <= b for a, b in zip(result, result[1:]))
    ),
)


def honest_sort(case):
    return sorted(case)


def pathological_sort(case):
    """Structurally valid, capability-safe, and semantically wrong.

    It returns a constant that happens to be the right answer for the one case
    the candidate chose to test itself against. Nothing about its shape, its
    imports, or its capability use distinguishes it from `honest_sort`.
    """
    return [1, 2, 3]


# The trial the candidate wrote for itself: one case, and it passes.
CANDIDATE_TRIAL = Trial(
    id="candidate-suite", provenance="generated.sort.v1", origin=CANDIDATE, cases=[[3, 1, 2]],
)

# Cases the candidate did not choose.
HELD_OUT_TRIAL = Trial(
    id="held-out-suite", provenance="evaluator.held-out", origin=INDEPENDENT,
    cases=[[3, 1, 2], [9, 8], [], [5, 5, 4], [1, 2, 3, 4]],
)


class LayerDistinctionTests(unittest.TestCase):
    """structural validity != capability safety != semantic Effect evidence."""

    def test_the_pathological_implementation_is_structurally_indistinguishable(self):
        """Both are plain callables over a list with no imports and no effects."""
        self.assertTrue(callable(honest_sort) and callable(pathological_sort))
        self.assertEqual([1, 2, 3], honest_sort([3, 1, 2]))
        self.assertEqual([1, 2, 3], pathological_sort([3, 1, 2]))

    def test_structural_and_capability_layers_can_pass_while_semantics_fail(self):
        result = run_trial(pathological_sort, HELD_OUT_TRIAL, ORDERED)
        decision = promote(
            ORDERED, [result], PromotionPolicy(), structural_ok=True, capability_ok=True,
        )
        self.assertEqual(REFUSED, decision.status)
        self.assertTrue(any(SEMANTIC in reason for reason in decision.reasons))

    def test_a_failed_structural_layer_refuses_on_its_own_terms(self):
        result = run_trial(honest_sort, HELD_OUT_TRIAL, ORDERED)
        decision = promote(
            ORDERED, [result], PromotionPolicy(), structural_ok=False, capability_ok=True,
        )
        self.assertEqual(REFUSED, decision.status)
        self.assertTrue(any("structural_validity" in reason for reason in decision.reasons))

    def test_a_failed_capability_layer_refuses_on_its_own_terms(self):
        result = run_trial(honest_sort, HELD_OUT_TRIAL, ORDERED)
        decision = promote(
            ORDERED, [result], PromotionPolicy(), structural_ok=True, capability_ok=False,
        )
        self.assertEqual(REFUSED, decision.status)
        self.assertTrue(any("capability_safety" in reason for reason in decision.reasons))


class AdversarialFixtureTests(unittest.TestCase):
    """The specimen: passes its own tests, violates the Effect's invariant."""

    def test_the_pathological_implementation_passes_its_own_suite(self):
        result = run_trial(pathological_sort, CANDIDATE_TRIAL, ORDERED)
        self.assertTrue(result.passed)
        self.assertEqual(1, result.cases_run)

    def test_the_independent_path_detects_it(self):
        result = run_trial(pathological_sort, HELD_OUT_TRIAL, ORDERED)
        self.assertFalse(result.passed)
        # Every case except the one it was written against.
        self.assertEqual(4, len(result.counterexamples))
        self.assertIn([9, 8], result.counterexamples)
        self.assertIn([], result.counterexamples)

    def test_the_honest_implementation_passes_both(self):
        self.assertTrue(run_trial(honest_sort, CANDIDATE_TRIAL, ORDERED).passed)
        self.assertTrue(run_trial(honest_sort, HELD_OUT_TRIAL, ORDERED).passed)

    def test_the_same_evidence_promotes_the_honest_one_and_refuses_the_other(self):
        policy = PromotionPolicy(minimum_cases=3)
        honest = promote(
            ORDERED, [run_trial(honest_sort, HELD_OUT_TRIAL, ORDERED)],
            policy, structural_ok=True, capability_ok=True,
        )
        pathological = promote(
            ORDERED, [run_trial(pathological_sort, HELD_OUT_TRIAL, ORDERED)],
            policy, structural_ok=True, capability_ok=True,
        )
        self.assertEqual(PROMOTED, honest.status)
        self.assertEqual(REFUSED, pathological.status)


class SelfCertificationTests(unittest.TestCase):
    def test_candidate_generated_tests_alone_cannot_promote(self):
        """The pathological implementation passes its own suite and is still refused."""
        result = run_trial(pathological_sort, CANDIDATE_TRIAL, ORDERED)
        self.assertTrue(result.passed)

        decision = promote(
            ORDERED, [result], PromotionPolicy(), structural_ok=True, capability_ok=True,
        )

        self.assertEqual(REFUSED, decision.status)
        self.assertEqual((), decision.counted)
        self.assertTrue(any("do not count" in reason for reason in decision.reasons))

    def test_candidate_evidence_is_recorded_even_though_it_does_not_count(self):
        """What was claimed is part of the account, including when it is discounted."""
        candidate = run_trial(pathological_sort, CANDIDATE_TRIAL, ORDERED)
        independent = run_trial(pathological_sort, HELD_OUT_TRIAL, ORDERED)

        decision = promote(
            ORDERED, [candidate, independent], PromotionPolicy(),
            structural_ok=True, capability_ok=True,
        )

        self.assertEqual(2, len(decision.recorded))
        self.assertEqual(1, len(decision.counted))
        self.assertEqual("candidate-suite", decision.recorded[0].trial_id)
        self.assertFalse(decision.recorded[0].independent)

    def test_an_honest_implementation_still_needs_independent_evidence(self):
        """Being right is not the same as being shown to be right."""
        decision = promote(
            ORDERED, [run_trial(honest_sort, CANDIDATE_TRIAL, ORDERED)],
            PromotionPolicy(), structural_ok=True, capability_ok=True,
        )
        self.assertEqual(REFUSED, decision.status)


class FailClosedTests(unittest.TestCase):
    def test_absent_semantic_evidence_refuses_rather_than_defers(self):
        decision = promote(
            ORDERED, [], PromotionPolicy(), structural_ok=True, capability_ok=True,
        )
        self.assertEqual(REFUSED, decision.status)
        self.assertTrue(any("independent trial(s) required" in reason for reason in decision.reasons))

    def test_a_trial_too_thin_to_discriminate_is_refused(self):
        thin = Trial(id="one-case", provenance="evaluator", origin=INDEPENDENT, cases=[[1]])
        decision = promote(
            ORDERED, [run_trial(honest_sort, thin, ORDERED)],
            PromotionPolicy(minimum_cases=3), structural_ok=True, capability_ok=True,
        )
        self.assertEqual(REFUSED, decision.status)
        self.assertTrue(any(BEHAVIOURAL in reason for reason in decision.reasons))

    def test_evidence_about_another_invariant_is_an_expression_error(self):
        other = EffectInvariant(id="something-else", description="d", check=lambda c, r: True)
        result = run_trial(honest_sort, HELD_OUT_TRIAL, other)
        with self.assertRaisesRegex(AlignmentError, "not 'ordered-permutation'"):
            promote(ORDERED, [result], PromotionPolicy(), structural_ok=True, capability_ok=True)

    def test_an_implementation_that_raises_yields_counterexamples_not_a_crash(self):
        def explodes(case):
            raise RuntimeError("boom")

        result = run_trial(explodes, HELD_OUT_TRIAL, ORDERED)
        self.assertFalse(result.passed)
        self.assertEqual(5, len(result.counterexamples))

    def test_malformed_trials_and_invariants_are_refused(self):
        with self.assertRaisesRegex(AlignmentError, "unknown trial origin"):
            Trial(id="t", provenance="p", origin="vibes", cases=[1])
        with self.assertRaisesRegex(AlignmentError, "at least one case"):
            Trial(id="t", provenance="p", origin=INDEPENDENT, cases=[])
        with self.assertRaisesRegex(AlignmentError, "requires provenance"):
            Trial(id="t", provenance="", origin=INDEPENDENT, cases=[1])
        with self.assertRaisesRegex(AlignmentError, "requires description"):
            EffectInvariant(id="i", description="", check=lambda c, r: True)


class HumanAcceptanceTests(unittest.TestCase):
    def test_human_acceptance_is_available_evidence_with_its_own_provenance(self):
        acceptance = HumanAcceptance(accepter="bdo", invariant_id=ORDERED.id, accepted=True,
                                     note="reviewed the counterexample set").as_result()
        self.assertEqual(HUMAN, acceptance.origin)
        self.assertEqual("bdo", acceptance.provenance)
        self.assertTrue(acceptance.independent)

    def test_a_policy_may_require_human_acceptance(self):
        machine = run_trial(honest_sort, HELD_OUT_TRIAL, ORDERED)
        policy = PromotionPolicy(require_human_acceptance=True)

        without = promote(ORDERED, [machine], policy, structural_ok=True, capability_ok=True)
        self.assertEqual(REFUSED, without.status)
        self.assertTrue(any("human acceptance" in reason for reason in without.reasons))

        accepted = HumanAcceptance("bdo", ORDERED.id, True).as_result()
        with_human = promote(ORDERED, [machine, accepted], policy,
                             structural_ok=True, capability_ok=True)
        self.assertEqual(PROMOTED, with_human.status)

    def test_low_stake_synthesis_does_not_require_a_human(self):
        """Fail-closed does not mean a person for every low-stake promotion."""
        decision = promote(
            ORDERED, [run_trial(honest_sort, HELD_OUT_TRIAL, ORDERED)],
            PromotionPolicy(require_human_acceptance=False),
            structural_ok=True, capability_ok=True,
        )
        self.assertEqual(PROMOTED, decision.status)

    def test_a_human_refusal_defeats_promotion(self):
        machine = run_trial(honest_sort, HELD_OUT_TRIAL, ORDERED)
        refused = HumanAcceptance("bdo", ORDERED.id, False, "not convinced").as_result()

        decision = promote(ORDERED, [machine, refused], PromotionPolicy(),
                           structural_ok=True, capability_ok=True)

        self.assertEqual(REFUSED, decision.status)
        self.assertTrue(any("defeated by" in reason for reason in decision.reasons))


class EvidenceProvenanceTests(unittest.TestCase):
    def test_a_result_identifies_its_evaluator_and_the_invariant_tested(self):
        described = run_trial(pathological_sort, HELD_OUT_TRIAL, ORDERED).as_dict()
        self.assertEqual("evaluator.held-out", described["provenance"])
        self.assertEqual(INDEPENDENT, described["origin"])
        self.assertEqual("ordered-permutation", described["invariant"])
        self.assertEqual(5, described["cases_run"])
        self.assertTrue(described["counterexamples"])

    def test_a_decision_serializes_counted_and_recorded_evidence_separately(self):
        candidate = run_trial(pathological_sort, CANDIDATE_TRIAL, ORDERED)
        independent = run_trial(pathological_sort, HELD_OUT_TRIAL, ORDERED)
        described = promote(ORDERED, [candidate, independent], PromotionPolicy(),
                            structural_ok=True, capability_ok=True).as_dict()

        self.assertEqual(REFUSED, described["status"])
        self.assertEqual(1, len(described["counted"]))
        self.assertEqual(2, len(described["recorded"]))
        self.assertTrue(described["reasons"])


if __name__ == "__main__":
    unittest.main()
