"""Independent post-execution observation/evaluation specimens for issue #35."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from cast.practitioner.brink_closure import (
    EnvironmentBrinkProbe,
    construct_attached_open_plan,
    observe_and_close,
)
from cast.practitioner.crossing import EvidenceContract, ManaParticipation, ResidualBounds
from cast.practitioner.handle_situation import resolve_handle_situation
from cast.practitioner.mana_cast import mana_cast_id
from cast.practitioner.observation import (
    CrossingObservationAccount,
    ExecutorClaim,
    ObservationAccountStore,
    ObservationEvaluationError,
    evaluate_crossing_observations,
)
from cast.practitioner.obligations import (
    CAPABILITY_GATE,
    DISCHARGED,
    NOT_APPLICABLE,
    STATE_PREDICATE,
    UNRESOLVED,
    VIOLATED,
    DischargeMechanism,
    RuntimeObligation,
)
from cast.practitioner.situation import CapabilityReceipt, Demand
from environment.consequence import RESIDUAL, ConsequenceFinding
from environment.magic import MagicLimits, MagicRuntime, MagicRuntimeError
from environment.observation import (
    OBSERVED,
    UNKNOWN,
    UNAVAILABLE,
    EnvironmentObservation,
    ObservationError,
    ObservationJournal,
    observer_is_independent,
)
from familiar.domain_handle import resolve_domain_handle


ROOT = Path(__file__).resolve().parents[2]
HANDLE_FIXTURES = ROOT / "familiar" / "domain_handle" / "fixtures"
ENV_FIXTURE = ROOT / "cast" / "tests" / "fixtures" / "domain-handle-environment-69.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def subject() -> dict:
    return {
        "familiar_format": "0.3",
        "id": "bdo.familiar",
        "caster": {"id": "bdo", "kind": "human"},
        "dialect": {"description": "compact distinction-first"},
        "attention": ["evidence crossings"],
        "preferences": ["small inspectable changes"],
        "stake": ["practitioner understanding"],
        "advisory_authority": ["presentation", "attention"],
    }


def handle() -> dict:
    return resolve_domain_handle(
        load_json(HANDLE_FIXTURES / "context.json"),
        load_json(HANDLE_FIXTURES / "domain-familiarity.json"),
        subject(),
    )


def fixture() -> dict:
    return load_json(ENV_FIXTURE)


def receipts(data: dict) -> tuple[CapabilityReceipt, ...]:
    values = []
    for raw in data["capability_receipts"]:
        item = deepcopy(raw)
        item["operations"] = tuple(item["operations"])
        values.append(CapabilityReceipt(**item))
    return tuple(values)


def demand() -> Demand:
    return Demand(
        operation="read",
        relation="permissions",
        capability="repository-read",
        environment="github",
        authority="read",
        subject="bdf1992/familiar",
        locator="bdf1992/familiar",
        capacity={"required": ["contents:read"]},
        attenuate=True,
    )


def situation_view() -> dict:
    data = fixture()
    intent = {
        "id": "observe-after-execution",
        "situation": {
            "id": "situation:35",
            "session_id": "session:35",
            "caster": {"id": "agent:test", "kind": "agent"},
            "target": {"repository": "bdf1992/familiar"},
            "environments": ["github"],
        },
        "expectations": [
            {
                "id": "environment-domain-role",
                "charted": {
                    "status": "present",
                    "path": ["context", "domains", "environment"],
                },
                "observation": "environment-domain-role",
                "compare_as": "value",
            }
        ],
    }
    return resolve_handle_situation(
        handle(),
        intent,
        data["observations"],
        receipts(data),
        {"repo-read-gate": demand()},
    )


def obligations() -> tuple[RuntimeObligation, ...]:
    return (
        RuntimeObligation(
            id="repo-read-gate",
            requirement_id="repository-readable",
            kind=CAPABILITY_GATE,
            phase="before",
            demand=demand(),
            spec={"purpose": "read exact repository"},
        ),
        RuntimeObligation(
            id="post-state",
            requirement_id="world-post-state",
            kind=STATE_PREDICATE,
            phase="after",
            spec={"expected": "ready"},
        ),
        RuntimeObligation(
            id="optional-after",
            requirement_id="optional-note",
            kind=STATE_PREDICATE,
            phase="after",
            required=False,
            spec={"expected": "anything"},
        ),
    )


def mechanisms() -> tuple[DischargeMechanism, ...]:
    return (
        DischargeMechanism(
            id="post-state-evaluator",
            kind=STATE_PREDICATE,
            provenance="environment:post-state-evaluator",
            evidence_contract="raw observation value equals sealed expected post-state",
            check=lambda obligation, context: context["observation_value"]
            == obligation.spec["expected"],
        ),
    )


def closed_attempt(contract_observer: str = "environment:post-state-evaluator"):
    view = situation_view()
    attached = construct_attached_open_plan(
        view,
        spell={"id": "spell:observe", "effect": "inspect"},
        technique={"id": "technique:github-read", "operation": "read"},
        obligations=obligations(),
        mechanisms=mechanisms(),
        mana=(ManaParticipation("network", "bdo", 3, 2),),
        evidence_contracts=(
            EvidenceContract(
                obligation_id="repo-read-gate",
                contract="exact capability match",
                observer="cast:capability-matcher",
            ),
            EvidenceContract(
                obligation_id="post-state",
                contract="independent observed post-state equals sealed expected value",
                observer=contract_observer,
            ),
        ),
        residual_bounds=ResidualBounds(("observed-residual",)),
        required_situation_evidence=("environment-domain-role",),
    )
    closed = observe_and_close(
        attached,
        view,
        effect_probe=EnvironmentBrinkProbe(
            kind="effect",
            environment="github",
            observer="environment:brink-effect",
            provenance="probe:brink-effect",
            read=lambda: 0,
        ),
        mana_probe=EnvironmentBrinkProbe(
            kind="mana",
            environment="github",
            observer="environment:brink-mana",
            provenance="probe:brink-mana",
            read=lambda: 0,
        ),
    )
    return view, attached, closed, mana_cast_id(closed)


def observation(
    cast_id: str,
    observation_id: str,
    value=None,
    *,
    status: str = OBSERVED,
    observer: str = "observer:independent-a",
    topic: str = "post-state",
) -> EnvironmentObservation:
    return EnvironmentObservation(
        id=observation_id,
        cast_id=cast_id,
        topic=topic,
        observer=observer,
        provenance=f"probe:{observation_id}",
        status=status,
        value=value,
        detail={"source": "synthetic Environment fixture"},
    )


def consequence(observer: str = "observer:consequence", mana_spent: int = 1) -> ConsequenceFinding:
    """Use a real valid #27 consequence while carrying #35 settlement evidence."""

    return ConsequenceFinding(
        kind=RESIDUAL,
        observer=observer,
        detail={
            "mana_spent": mana_spent,
            "observation": "independent consequence",
        },
    )


def evaluate(
    observations: tuple[EnvironmentObservation, ...],
    *,
    executor_claim: ExecutorClaim | None = None,
    consequence_finding: ConsequenceFinding | None = None,
    contract_observer: str = "environment:post-state-evaluator",
):
    _view, _attached, closed, cast_id = closed_attempt(contract_observer)
    account = evaluate_crossing_observations(
        closed,
        cast_id,
        executor_claim=executor_claim or ExecutorClaim(True, result={"claimed_state": "ready"}),
        observations=observations,
        consequence=consequence_finding or consequence(),
        mana_participant="bdo",
    )
    return closed, cast_id, account


class StatusTests(unittest.TestCase):
    def test_all_four_obligation_statuses_are_representable(self):
        _closed, cast_id = closed_attempt()[2:4]

        discharged = evaluate((observation(cast_id, "discharged", "ready"),))[2]
        violated = evaluate((observation(cast_id, "violated", "broken"),))[2]
        unresolved = evaluate(
            (observation(cast_id, "unavailable", status=UNAVAILABLE),)
        )[2]

        self.assertEqual(DISCHARGED, next(f for f in discharged.obligation_findings if f.obligation_id == "post-state").status)
        self.assertEqual(VIOLATED, next(f for f in violated.obligation_findings if f.obligation_id == "post-state").status)
        self.assertEqual(UNRESOLVED, next(f for f in unresolved.obligation_findings if f.obligation_id == "post-state").status)
        self.assertEqual(NOT_APPLICABLE, next(f for f in discharged.obligation_findings if f.obligation_id == "optional-after").status)

    def test_unavailable_and_unknown_remain_explicit_unknown_space(self):
        _view, _attached, _closed, cast_id = closed_attempt()
        account = evaluate(
            (
                observation(cast_id, "unknown", status=UNKNOWN),
                observation(cast_id, "unavailable", status=UNAVAILABLE),
            )
        )[2]

        self.assertIn("unknown", account.unknown)
        self.assertIn("unavailable", account.unknown)
        self.assertIn("post-state", account.unknown)
        finding = next(f for f in account.obligation_findings if f.obligation_id == "post-state")
        self.assertEqual(UNRESOLVED, finding.status)
        self.assertCountEqual(["unknown", "unavailable"], finding.detail["unknown_or_unavailable"])


class EvidenceBindingTests(unittest.TestCase):
    def test_finding_binds_raw_observation_evaluator_status_provenance_and_sealed_contract(self):
        _view, _attached, closed, cast_id = closed_attempt()
        raw = observation(cast_id, "obs:bound", "ready")
        account = evaluate_crossing_observations(
            closed,
            cast_id,
            executor_claim=ExecutorClaim(True, result="executor says done"),
            observations=(raw,),
            consequence=consequence(),
            mana_participant="bdo",
        )
        finding = next(f for f in account.obligation_findings if f.obligation_id == "post-state")

        self.assertEqual(("obs:bound",), finding.observation_ids)
        self.assertEqual("post-state-evaluator", finding.evaluator_id)
        self.assertEqual("environment:post-state-evaluator", finding.evaluator_provenance)
        self.assertEqual("environment:post-state-evaluator", finding.evidence_contract["observer"])
        self.assertEqual(DISCHARGED, finding.status)
        self.assertEqual("probe:obs:bound", account.observations[0].provenance)
        self.assertEqual(closed.digest, account.plan_digest)
        self.assertTrue(account.digest.startswith("sha256:"))

    def test_sealed_evidence_contract_cannot_be_replaced_through_open_plan_after_closure(self):
        _view, attached, closed, cast_id = closed_attempt()
        original = closed.plan.evidence_contract_for("post-state").observer
        open_contract = next(c for c in attached.plan.evidence_contracts if c.obligation_id == "post-state")
        object.__setattr__(open_contract, "observer", "technique:forged-after-execution")

        account = evaluate_crossing_observations(
            closed,
            cast_id,
            executor_claim=ExecutorClaim(True),
            observations=(observation(cast_id, "obs:still-bound", "ready"),),
            consequence=consequence(),
            mana_participant="bdo",
        )
        finding = next(f for f in account.obligation_findings if f.obligation_id == "post-state")
        self.assertEqual("environment:post-state-evaluator", original)
        self.assertEqual(original, finding.evidence_contract["observer"])

    def test_evaluator_not_matching_sealed_contract_fails_closed(self):
        _view, _attached, closed, cast_id = closed_attempt("environment:other-evaluator")
        with self.assertRaisesRegex(ObservationEvaluationError, "sealed evidence evaluator mismatch"):
            evaluate_crossing_observations(
                closed,
                cast_id,
                executor_claim=ExecutorClaim(True),
                observations=(observation(cast_id, "obs:mismatch", "ready"),),
                consequence=consequence(),
                mana_participant="bdo",
            )


class IndependenceAndDisagreementTests(unittest.TestCase):
    def test_participant_caster_or_technique_cannot_discharge_own_obligation(self):
        _view, _attached, closed, cast_id = closed_attempt()
        for principal in ("bdo", "agent:test", "technique:github-read"):
            with self.subTest(principal=principal):
                account = evaluate_crossing_observations(
                    closed,
                    cast_id,
                    executor_claim=ExecutorClaim(True),
                    observations=(
                        observation(cast_id, f"self:{principal}", "ready", observer=principal),
                    ),
                    consequence=consequence(),
                    mana_participant="bdo",
                )
                finding = next(f for f in account.obligation_findings if f.obligation_id == "post-state")
                self.assertEqual(UNRESOLVED, finding.status)
                self.assertEqual([f"self:{principal}"], finding.detail["self_observation_rejected"])

    def test_consequence_observer_must_also_be_independent(self):
        _view, _attached, closed, cast_id = closed_attempt()
        for principal in ("bdo", "agent:test", "technique:github-read"):
            with self.subTest(principal=principal):
                with self.assertRaisesRegex(ObservationEvaluationError, "consequence observer is not independent"):
                    evaluate_crossing_observations(
                        closed,
                        cast_id,
                        executor_claim=ExecutorClaim(True),
                        observations=(observation(cast_id, "obs:ok", "ready"),),
                        consequence=consequence(observer=principal),
                        mana_participant="bdo",
                    )

    def test_two_independent_observers_may_disagree_without_overwrite(self):
        _view, _attached, closed, cast_id = closed_attempt()
        first = observation(cast_id, "observer:a", "ready", observer="observer:a")
        second = observation(cast_id, "observer:b", "broken", observer="observer:b")
        account = evaluate_crossing_observations(
            closed,
            cast_id,
            executor_claim=ExecutorClaim(True),
            observations=(first, second),
            consequence=consequence(),
            mana_participant="bdo",
        )

        finding = next(f for f in account.obligation_findings if f.obligation_id == "post-state")
        self.assertEqual(UNRESOLVED, finding.status)
        self.assertEqual("independent observers disagree", finding.detail["reason"])
        self.assertEqual(("observer:a", "observer:b"), finding.observation_ids)
        self.assertEqual(2, len(account.observations))

    def test_journal_is_append_only_and_preserves_conflicting_records(self):
        _view, _attached, _closed, cast_id = closed_attempt()
        journal = ObservationJournal()
        journal.append(observation(cast_id, "journal:a", "ready", observer="observer:a"))
        journal.append(observation(cast_id, "journal:b", "broken", observer="observer:b"))
        self.assertEqual(2, len(journal.for_cast(cast_id, "post-state")))
        with self.assertRaisesRegex(ObservationError, "already recorded"):
            journal.append(observation(cast_id, "journal:a", "different", observer="observer:c"))

    def test_common_independence_predicate_has_one_elementary_meaning(self):
        self.assertTrue(observer_is_independent("observer", "caster", "technique", "participant"))
        self.assertFalse(observer_is_independent("caster", "caster", "technique", "participant"))
        self.assertFalse(observer_is_independent("", "caster"))


class ExecutorClaimAndSettlementTests(unittest.TestCase):
    def test_executor_success_is_preserved_as_claim_when_independent_observation_violates(self):
        _view, _attached, closed, cast_id = closed_attempt()
        account = evaluate_crossing_observations(
            closed,
            cast_id,
            executor_claim=ExecutorClaim(True, result={"claimed_state": "ready"}),
            observations=(observation(cast_id, "obs:world-says-broken", "broken"),),
            consequence=consequence(mana_spent=1),
            mana_participant="bdo",
        )
        finding = next(f for f in account.obligation_findings if f.obligation_id == "post-state")

        self.assertTrue(account.executor_claim.succeeded)
        self.assertEqual({"claimed_state": "ready"}, account.executor_claim.result)
        self.assertEqual(VIOLATED, finding.status)

    def test_magic_settlement_consumes_evaluated_account_not_executor_success(self):
        _view, _attached, closed, cast_id = closed_attempt()
        store = ObservationAccountStore()
        magic = MagicRuntime(
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
            consequence_verifier=store.consequence_decision,
        )
        magic.claim("bdo", "network", 3)
        magic.commit(cast_id, "bdo", "network", 2)

        account = evaluate_crossing_observations(
            closed,
            cast_id,
            executor_claim=ExecutorClaim(True, result="executor reports success"),
            observations=(observation(cast_id, "obs:settlement", "ready"),),
            consequence=consequence(mana_spent=1),
            mana_participant="bdo",
        )
        store.put(account)
        event = magic.settle(cast_id)

        self.assertEqual(1, event.details["spent"])
        self.assertEqual(1, event.details["released"])
        self.assertEqual(
            f"observation-account:{account.digest}",
            event.details["decision"]["receipt_id"],
        )
        self.assertEqual(20, magic.total())

    def test_missing_evaluated_account_leaves_commitment_live(self):
        _view, _attached, _closed, cast_id = closed_attempt()
        store = ObservationAccountStore()
        magic = MagicRuntime(
            20,
            MagicLimits(12, 10, 6, 3, 5, 2, 3, 1),
            initial_locality="network",
            access_resolver=lambda actor, operation, locality: actor == "bdo" and locality == "network",
            consequence_verifier=store.consequence_decision,
        )
        magic.claim("bdo", "network", 3)
        magic.commit(cast_id, "bdo", "network", 2)

        with self.assertRaisesRegex(MagicRuntimeError, "no evaluated observation account"):
            magic.settle(cast_id)
        self.assertEqual(2, magic.committed_by("bdo"))
        self.assertEqual(20, magic.total())

    def test_store_refuses_a_second_different_account_for_same_cast(self):
        _view, _attached, closed, cast_id = closed_attempt()
        store = ObservationAccountStore()
        first = evaluate_crossing_observations(
            closed,
            cast_id,
            executor_claim=ExecutorClaim(True),
            observations=(observation(cast_id, "obs:first", "ready"),),
            consequence=consequence(mana_spent=1),
            mana_participant="bdo",
        )
        second = evaluate_crossing_observations(
            closed,
            cast_id,
            executor_claim=ExecutorClaim(False, error_type="RuntimeError"),
            observations=(observation(cast_id, "obs:second", "broken"),),
            consequence=consequence(mana_spent=0),
            mana_participant="bdo",
        )
        store.put(first)
        with self.assertRaisesRegex(ObservationEvaluationError, "already exists"):
            store.put(second)
        self.assertEqual(first.digest, store.get(cast_id).digest)


if __name__ == "__main__":
    unittest.main()
