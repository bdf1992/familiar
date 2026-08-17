"""Cross-claim adversarial conformance suite for the 0.7 Work crossing (#37).

Issue-level tests prove mechanisms locally. This suite attacks the relations
between those mechanisms and carries one provider-neutral Mana-bearing attempt
from an already closed plan through execution claim, independent observation,
settlement, and immutable CAST sealing.

A defeating specimen need not be a valid runtime input. Its job is to make one
normative claim false in a controlled way and prove the conformance boundary can
name that failure rather than silently harmonize it.
"""

from __future__ import annotations

from dataclasses import replace
import unittest

from cast.practitioner.brink_closure import construct_attached_open_plan
from cast.practitioner.cast_record import CastSealingError, seal_crossing
from cast.practitioner.crossing import canonical_material
from cast.practitioner.observation import (
    ExecutorClaim,
    ObservationAccountStore,
    evaluate_crossing_observations,
)
from cast.practitioner.obligations import RuntimeObligation
from cast.practitioner.situation_crossing import SituationCrossingError
from environment.authority import (
    AttenuatedCredentialBoundary,
    AuthorityViolationError,
    RecordingHostCredential,
)
from environment.magic import MagicLimits, MagicRuntime, MagicRuntimeError
from environment.mana_tensor import ManaCoordinate, ManaTensor, ManaTerm
from environment.scope import MappingScopeBoundary, ScopeViolationError
from test_observation_35 import (
    closed_attempt,
    consequence,
    mechanisms,
    obligations,
    observation,
    situation_view,
)


class ConformanceFailure(AssertionError):
    """A synthetic specimen defeats one required 0.7 protocol claim."""


def assert_requirement_coverage(closed, required_requirement_ids: tuple[str, ...]) -> None:
    """External witness for Claim 1 until #56 supplies the adopted declaration.

    The current Work plan carries typed obligations and their `requirement_id`,
    but portable declaration adoption is explicitly still open. The conformance
    suite therefore supplies the required ids as the oracle and tests the exact
    relation that #38/#56 must wire to the adopted declaration source.
    """

    represented = {
        binding.obligation.requirement_id
        for binding in closed.plan.obligations.bindings.values()
    }
    missing = sorted(set(required_requirement_ids) - represented)
    if missing:
        raise ConformanceFailure(
            "required properties have no RuntimeObligation: " + ", ".join(missing)
        )


def magic_runtime(store: ObservationAccountStore | None = None) -> MagicRuntime:
    return MagicRuntime(
        20,
        MagicLimits(
            max_network=12,
            max_local=10,
            max_personal=6,
            max_cast=3,
            max_committed=5,
            max_restored=2,
            max_level=3,
            drain_rate=1,
        ),
        initial_locality="network",
        access_resolver=lambda actor, operation, locality: actor == "bdo" and locality == "network",
        consequence_verifier=store.consequence_decision if store is not None else None,
    )


def complete_crossing(*, executor_success: bool = True, observed_value: str = "ready"):
    """One real Mana-bearing crossing from ClosedPlan through immutable CAST."""

    _view, _attached, closed, cast_id = closed_attempt()
    store = ObservationAccountStore()
    magic = magic_runtime(store)

    claim_event = magic.claim("bdo", "network", 3)
    commit_event = magic.commit(cast_id, "bdo", "network", 2)

    # Technique execution is represented by its claim only here. #38 owns the
    # reference-Kernel call path; #35 owns whether that claim matches the world.
    claim = ExecutorClaim(
        executor_success,
        result={"technique": "returned"} if executor_success else None,
        error_type=None if executor_success else "RuntimeError",
        error_message=None if executor_success else "synthetic post-effect failure",
    )
    account = evaluate_crossing_observations(
        closed,
        cast_id,
        executor_claim=claim,
        observations=(observation(cast_id, "conformance:post-state", observed_value),),
        consequence=consequence(mana_spent=1),
        mana_participant="bdo",
    )
    store.put(account)
    settle_event = magic.settle(cast_id)

    record = seal_crossing(
        closed,
        account,
        mana_events=(commit_event, settle_event),
        residuals=({"kind": "observed-residual", "present": True},),
        execution_trace=({"step": "executor returned" if executor_success else "executor raised"},),
    )
    return closed, cast_id, magic, account, record, claim_event, commit_event, settle_event


class CompleteCrossingTests(unittest.TestCase):
    def test_one_happy_path_exercises_the_complete_work_crossing(self):
        closed, cast_id, magic, account, sealed, claim_event, commit_event, settle_event = complete_crossing()
        record = sealed.material()

        self.assertEqual("claim", claim_event.operation)
        self.assertEqual("commit", commit_event.operation)
        self.assertEqual("settle", settle_event.operation)
        self.assertEqual(closed.digest, account.plan_digest)
        self.assertEqual(closed.digest, record["plan_digest"])
        self.assertEqual(cast_id, record["cast_id"])
        self.assertEqual("successful", record["status"])
        self.assertEqual(["commit", "settle"], [event["operation"] for event in record["mana_transitions"]])
        self.assertEqual(1, record["mana_settlement"]["details"]["spent"])
        self.assertEqual(1, record["mana_settlement"]["details"]["released"])
        self.assertEqual(20, magic.total())
        self.assertTrue(sealed.record_digest.startswith("sha256:"))


class Claim1RequirementObligationTests(unittest.TestCase):
    def test_valid_specimen_accounts_for_every_required_property(self):
        closed = closed_attempt()[2]
        assert_requirement_coverage(
            closed,
            ("repository-readable", "world-post-state"),
        )

    def test_defeat_missing_required_property_is_detectable_even_after_closure(self):
        closed = closed_attempt()[2]
        with self.assertRaisesRegex(ConformanceFailure, "declared-but-dropped"):
            assert_requirement_coverage(
                closed,
                ("repository-readable", "world-post-state", "declared-but-dropped"),
            )


class Claim2ExactCapabilityBindingTests(unittest.TestCase):
    def test_valid_specimen_retains_exact_receipt_and_attenuated_handle(self):
        closed = closed_attempt()[2]
        match = closed.plan.obligations.capability_plan.matches["repo-read-gate"]
        self.assertEqual("repository-read", match.receipt.name)
        self.assertEqual("repository-read (attenuated)", match.handle.name)
        self.assertTrue(match.attenuated)
        self.assertEqual({"granted": ("contents:read",)}, dict(match.handle.capacity))

    def test_defeat_changed_demand_cannot_rebind_from_same_situation(self):
        view = situation_view()
        changed: list[RuntimeObligation] = list(obligations())
        gate = changed[0]
        changed_demand = replace(
            gate.demand,
            capacity={"required": ["contents:read", "administration:write"]},
        )
        changed[0] = replace(gate, demand=changed_demand)

        baseline = closed_attempt()[2].plan
        with self.assertRaises(SituationCrossingError):
            construct_attached_open_plan(
                view,
                spell={"id": "spell:conformance", "effect": "inspect"},
                technique={"id": "technique:github-read", "operation": "read"},
                obligations=tuple(changed),
                mechanisms=mechanisms(),
                mana=baseline.mana,
                evidence_contracts=baseline.evidence_contracts,
                residual_bounds=baseline.residual_bounds,
                required_situation_evidence=("environment-domain-role",),
            )


class Claim3EffectPathAttenuationTests(unittest.TestCase):
    def test_valid_scope_and_authority_handles_transfer_only_resolved_effects(self):
        target = {"allowed": 0, "forbidden": 0}
        scope = MappingScopeBoundary(target, ("allowed",))
        host = RecordingHostCredential()
        authority = AttenuatedCredentialBoundary(host, ("write",), resources=("allowed",))

        scope.handle()["allowed"] = 1
        authority.handle().act("write", "allowed")

        self.assertEqual(1, target["allowed"])
        self.assertEqual([("write", "allowed")], host.acts)
        self.assertEqual((), scope.violations())
        self.assertEqual((), authority.violations())

    def test_defeat_out_of_scope_and_out_of_authority_direct_effects_are_blocked_and_visible(self):
        target = {"allowed": 0, "forbidden": 0}
        scope = MappingScopeBoundary(target, ("allowed",))
        host = RecordingHostCredential()
        authority = AttenuatedCredentialBoundary(host, ("write",), resources=("allowed",))

        # A dishonest Technique may swallow both failures. The Environment still
        # prevents the direct consequence and retains the attempts.
        try:
            scope.handle()["forbidden"] = 9
        except ScopeViolationError:
            pass
        try:
            authority.handle().act("delete", "allowed")
        except AuthorityViolationError:
            pass

        self.assertEqual(0, target["forbidden"])
        self.assertEqual([], host.acts)
        self.assertEqual("forbidden", str(scope.violations()[0].key))
        self.assertEqual("delete", authority.violations()[0].permission)


class Claim4ManaClosureConservationTests(unittest.TestCase):
    def test_valid_commit_and_settlement_preserve_one_shared_total(self):
        _closed, _cast_id, magic, _account, _record, _claim, _commit, _settle = complete_crossing()
        self.assertEqual(20, magic.total())

    def test_defeat_same_cast_cannot_commit_twice(self):
        _view, _attached, _closed, cast_id = closed_attempt()
        magic = magic_runtime()
        magic.claim("bdo", "network", 3)
        magic.commit(cast_id, "bdo", "network", 2)
        before = magic.total()
        with self.assertRaises(MagicRuntimeError):
            magic.commit(cast_id, "bdo", "network", 1)
        self.assertEqual(before, magic.total())
        self.assertEqual(20, magic.total())

    def test_preclosure_refusal_has_no_cast_mana_transition(self):
        magic = magic_runtime()
        magic.claim("bdo", "network", 3)
        before = magic.total()
        # Refusal occurs before a cast id is committed. The pre-existing claim is
        # not Cast-attributable movement and remains exactly where it was.
        self.assertEqual(0, magic.committed_by("bdo"))
        self.assertEqual(before, magic.total())


class Claim5IndependentObservationTests(unittest.TestCase):
    def test_defeat_executor_success_cannot_override_independent_violation(self):
        closed, _cast_id, _magic, account, _sealed, _claim, _commit, _settle = complete_crossing(observed_value="broken")
        self.assertTrue(account.executor_claim.succeeded)
        finding = next(item for item in account.obligation_findings if item.obligation_id == "post-state")
        self.assertEqual("violated", finding.status)
        record = seal_crossing(closed, account).material()
        self.assertEqual("violated", record["status"])

    def test_defeat_self_observation_cannot_discharge(self):
        _view, _attached, closed, cast_id = closed_attempt()
        account = evaluate_crossing_observations(
            closed,
            cast_id,
            executor_claim=ExecutorClaim(True),
            observations=(observation(cast_id, "self", "ready", observer="agent:test"),),
            consequence=consequence(),
            mana_participant="bdo",
        )
        finding = next(item for item in account.obligation_findings if item.obligation_id == "post-state")
        self.assertEqual("unresolved", finding.status)
        self.assertEqual(["self"], finding.detail["self_observation_rejected"])

    def test_post_effect_executor_failure_still_observes_settles_and_seals(self):
        _closed, _cast_id, magic, account, sealed, _claim, _commit, settle = complete_crossing(executor_success=False)
        record = sealed.material()
        self.assertFalse(account.executor_claim.succeeded)
        self.assertEqual("residual", account.consequence["kind"])
        self.assertEqual(1, settle.details["spent"])
        self.assertEqual(1, settle.details["released"])
        self.assertEqual("aborted", record["status"])
        self.assertEqual("residual", record["outcome"]["consequence"]["kind"])
        self.assertEqual(20, magic.total())


class Claim6FaithfulSealingTests(unittest.TestCase):
    def test_valid_record_recovers_every_crossing_evidence_family(self):
        closed, cast_id, _magic, account, sealed, _claim, _commit, _settle = complete_crossing()
        record = sealed.material()

        self.assertEqual(closed.digest, record["plan_digest"])
        self.assertEqual(closed.plan.configuration, record["recorded_configuration"])
        self.assertEqual(
            set(closed.plan.obligations.capability_plan.matches),
            set(record["capability_match_evidence"]),
        )
        self.assertEqual(len(account.observations), len(record["observations"]))
        self.assertEqual(len(account.obligation_findings), len(record["obligation_findings"]))
        self.assertEqual(account.consequence, record["outcome"]["consequence"])
        self.assertEqual(cast_id, record["cast_id"])
        self.assertIsNotNone(record["mana_settlement"])
        self.assertTrue(record["residuals"])

    def test_defeat_sealed_readback_mutation_cannot_change_identity_or_state(self):
        sealed = complete_crossing()[4]
        before = sealed.material()
        readback = sealed.material()
        readback["recorded_configuration"]["target"] = {"forged": True}
        readback["status"] = "successful" if before["status"] != "successful" else "violated"

        self.assertEqual(before, sealed.material())
        self.assertEqual(before["record_digest"], sealed.record_digest)

    def test_defeat_observation_account_from_another_plan_cannot_seal(self):
        closed, _cast_id, _magic, account, _sealed, _claim, _commit, _settle = complete_crossing()
        forged = replace(account, plan_digest="sha256:" + "0" * 64)
        with self.assertRaises(CastSealingError):
            seal_crossing(closed, forged)


class AlgebraSeparationTests(unittest.TestCase):
    def test_capacity_obligations_and_mana_remain_separate_closed_plan_algebras(self):
        closed = closed_attempt()[2]
        material = canonical_material(closed.plan)
        self.assertEqual(
            {
                "crossing_plan_version",
                "configuration",
                "capacity",
                "obligations",
                "mana",
                "evidence_contracts",
                "residual_bounds",
            },
            set(material),
        )
        self.assertNotEqual(material["capacity"], material["obligations"])
        self.assertNotEqual(material["capacity"], material["mana"])
        self.assertNotEqual(material["obligations"], material["mana"])

    def test_equal_scalar_cost_does_not_imply_equal_mana_composition(self):
        ambient = ManaCoordinate(runtime="r", locality="network", disposition="ambient", relation="ambient")
        first = ManaTensor(
            10,
            (
                ManaTerm(ambient, 8),
                ManaTerm(ManaCoordinate(cast="cast:a", component="material", runtime="r", locality="network", disposition="committed", relation="component"), 1),
                ManaTerm(ManaCoordinate(cast="cast:a", component="verbal", runtime="r", locality="network", disposition="committed", relation="component"), 1),
            ),
        )
        second = ManaTensor(
            10,
            (
                ManaTerm(ambient, 8),
                ManaTerm(ManaCoordinate(cast="cast:b", component="focus", runtime="r", locality="network", disposition="committed", relation="component"), 2),
            ),
        )

        self.assertEqual(2, first.cast_cost("cast:a"))
        self.assertEqual(2, second.cast_cost("cast:b"))
        self.assertNotEqual(first.composition(cast="cast:a"), second.composition(cast="cast:b"))

    def test_heterogeneous_capacity_does_not_enter_mana_conservation_equation(self):
        view = situation_view()
        capacity = view["environment"]["capability_receipts"][0]["capacity"]
        magic = magic_runtime()
        before = magic.total()

        # Arbitrarily rich capacity evidence remains situated mechanism data.
        capacity["wall_clock_ms"] = 5000
        capacity["usd_ceiling"] = 25
        capacity["model_tokens"] = 32000

        self.assertEqual(5000, capacity["wall_clock_ms"])
        self.assertEqual(25, capacity["usd_ceiling"])
        self.assertEqual(32000, capacity["model_tokens"])
        self.assertEqual(before, magic.total())
        self.assertEqual(20, magic.total())
        self.assertEqual(0, magic.committed_by("bdo"))


if __name__ == "__main__":
    unittest.main()
