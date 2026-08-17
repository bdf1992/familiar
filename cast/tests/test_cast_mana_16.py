"""Invariant Cast <-> conserved Mana integration specimens for issue #16."""

from __future__ import annotations

import ast
from copy import deepcopy
import json
from pathlib import Path
import unittest

from cast.practitioner.brink_closure import (
    EnvironmentBrinkProbe,
    construct_attached_open_plan,
)
from cast.practitioner.crossing import EvidenceContract, ManaParticipation, ResidualBounds
from cast.practitioner.handle_situation import resolve_handle_situation
from cast.practitioner.mana_cast import (
    ManaCastError,
    admit_mana_before_closure,
    mana_cast_id,
    run_mana_cast,
    settle_mana_cast,
)
from cast.practitioner.obligations import CAPABILITY_GATE, RuntimeObligation
from cast.practitioner.situation import CapabilityReceipt, Demand
from environment.magic import ConsequenceDecision, MagicLimits, MagicRuntime, MagicRuntimeError
from familiar.domain_handle import resolve_domain_handle


ROOT = Path(__file__).resolve().parents[2]
HANDLE_FIXTURES = ROOT / "familiar" / "domain_handle" / "fixtures"
ENV_FIXTURE = ROOT / "cast" / "tests" / "fixtures" / "domain-handle-environment-69.json"
SEAM = ROOT / "cast" / "practitioner" / "mana_cast.py"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def limits(**overrides) -> MagicLimits:
    values = {
        "max_network": 12,
        "max_local": 10,
        "max_personal": 6,
        "max_cast": 3,
        "max_committed": 5,
        "max_restored": 2,
        "max_level": 3,
        "drain_rate": 1,
    }
    values.update(overrides)
    return MagicLimits(**values)


def subject(subject_id: str = "bdo") -> dict:
    return {
        "familiar_format": "0.3",
        "id": f"{subject_id}.familiar",
        "caster": {"id": subject_id, "kind": "human"},
        "dialect": {"description": "compact distinction-first"},
        "attention": ["runtime crossings"],
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


def env_fixture() -> dict:
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


def situation_view(attempt: str = "a") -> dict:
    data = env_fixture()
    intent = {
        "id": f"mana-cast:{attempt}",
        "situation": {
            "id": f"situation:mana:{attempt}",
            "session_id": f"session:mana:{attempt}",
            "caster": {"id": "agent:test", "kind": "agent"},
            "target": {"repository": "bdf1992/familiar", "attempt": attempt},
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


def obligation() -> RuntimeObligation:
    return RuntimeObligation(
        id="repo-read-gate",
        requirement_id="repository-readable",
        kind=CAPABILITY_GATE,
        phase="before",
        demand=demand(),
        spec={"purpose": "read exact repository"},
    )


def attached(
    attempt: str = "a",
    *,
    mana: tuple[ManaParticipation, ...] | None = None,
):
    view = situation_view(attempt)
    if mana is None:
        mana = (
            ManaParticipation(
                locality="network",
                participant="bdo",
                claim=3,
                commit=2,
            ),
        )
    attachment = construct_attached_open_plan(
        view,
        spell={"id": "spell:mana-integration", "effect": "inspect"},
        technique={"id": "technique:mana-test", "operation": "read"},
        obligations=(obligation(),),
        mana=mana,
        evidence_contracts=(
            EvidenceContract(
                obligation_id="repo-read-gate",
                contract="exact capability matcher evidence",
                observer="cast:capability-matcher",
            ),
        ),
        residual_bounds=ResidualBounds(("test-effect",)),
        required_situation_evidence=("environment-domain-role",),
    )
    return view, attachment


def probe(kind: str, read=None):
    return EnvironmentBrinkProbe(
        kind=kind,
        environment="github",
        observer=f"environment:{kind}-observer",
        provenance=f"test:{kind}-probe",
        read=(lambda: 0) if read is None else read,
    )


class ConsequenceRouter:
    """One shared Environment verifier routing independent decisions by cast id."""

    def __init__(self):
        self.effects: dict[str, int] = {}
        self.available = True
        self.confirmed = True
        self.calls: list[str] = []

    def __call__(self, cast_id: str, commitment: dict) -> ConsequenceDecision:
        self.calls.append(cast_id)
        if not self.available:
            raise MagicRuntimeError("consequence observation unavailable")
        spent = min(self.effects.get(cast_id, 0), commitment["amount"])
        return ConsequenceDecision(
            confirmed=self.confirmed,
            spent=spent if self.confirmed else 0,
            observer="environment:consequence-observer",
            receipt_id=f"consequence:{cast_id}:{len(self.calls)}",
            reason="independent observed consequence",
        )


def runtime(router: ConsequenceRouter | None = None, **limit_overrides) -> MagicRuntime:
    router = router or ConsequenceRouter()
    return MagicRuntime(
        20,
        limits(**limit_overrides),
        initial_locality="network",
        access_resolver=lambda actor, operation, locality: actor == "bdo" and locality == "network",
        consequence_verifier=router,
    )


class AdmissionTests(unittest.TestCase):
    def test_cast_does_not_auto_claim_and_insufficient_claim_refuses_before_brink(self):
        view, attachment = attached()
        magic = runtime()
        probes = {"effect": 0, "mana": 0}

        with self.assertRaisesRegex(ManaCastError, "insufficient pre-existing Claim"):
            run_mana_cast(
                attachment,
                view,
                magic,
                effect_probe=probe("effect", read=lambda: probes.__setitem__("effect", probes["effect"] + 1) or 0),
                mana_probe=probe("mana", read=lambda: probes.__setitem__("mana", probes["mana"] + 1) or 0),
                executor=lambda *_: self.fail("executor must not run"),
            )

        self.assertEqual({"effect": 0, "mana": 0}, probes)
        self.assertEqual(0, magic.claimed_by("bdo", locality="network"))
        self.assertNotIn("claim", [event.operation for event in magic.events[1:]])

    def test_preexisting_claim_and_caps_are_checked_without_moving_mana(self):
        view, attachment = attached()
        magic = runtime()
        magic.claim("bdo", "network", 3)
        before = tuple(magic.events)
        admission = admit_mana_before_closure(attachment, view, magic)

        self.assertEqual(3, admission.observed_claimed)
        self.assertEqual(3, admission.claim_basis)
        self.assertEqual(2, admission.commit)
        self.assertEqual(before, magic.events)
        self.assertEqual(20, magic.total())

    def test_max_cast_refuses_before_closure_or_mana_transition(self):
        view, attachment = attached()
        magic = runtime(max_cast=1)
        magic.claim("bdo", "network", 3)
        before = tuple(magic.events)

        with self.assertRaisesRegex(ManaCastError, "exceeds max_cast"):
            admit_mana_before_closure(attachment, view, magic)

        self.assertEqual(before, magic.events)

    def test_network_committed_capacity_is_preflighted_from_public_ledger(self):
        view, attachment = attached()
        magic = runtime(max_committed=2)
        magic.claim("bdo", "network", 4)
        magic.commit("other-cast", "bdo", "network", 1)

        with self.assertRaisesRegex(ManaCastError, "remaining max_committed"):
            admit_mana_before_closure(attachment, view, magic)

    def test_multiple_mana_participations_are_refused_not_flattened(self):
        participation = (
            ManaParticipation("network", "bdo", 2, 1),
            ManaParticipation("lab", "other", 2, 1),
        )
        view, attachment = attached(mana=participation)
        magic = runtime()
        magic.claim("bdo", "network", 3)

        with self.assertRaisesRegex(ManaCastError, "exactly one ManaParticipation"):
            admit_mana_before_closure(attachment, view, magic)

    def test_zero_mana_semantics_are_not_silently_defined_by_this_integration(self):
        view, attachment = attached(mana=(ManaParticipation("network", "bdo", 0, 0),))
        magic = runtime()
        with self.assertRaisesRegex(ManaCastError, "zero-Mana semantics are outside #16"):
            admit_mana_before_closure(attachment, view, magic)


class OrderedTransitionTests(unittest.TestCase):
    def test_commit_is_first_cast_mana_transition_and_executor_sees_it(self):
        router = ConsequenceRouter()
        magic = runtime(router)
        magic.claim("bdo", "network", 3)
        view, attachment = attached()
        observations: list[tuple[str, int, int]] = []

        def executor(closed, cast_id):
            observations.append(
                (
                    magic.events[-1].operation,
                    magic.claimed_by("bdo", locality="network"),
                    magic.committed_by("bdo"),
                )
            )
            router.effects[cast_id] = 1
            return {"effect": "applied"}

        result = run_mana_cast(
            attachment,
            view,
            magic,
            effect_probe=probe("effect"),
            mana_probe=probe("mana"),
            executor=executor,
        )

        self.assertEqual([("commit", 1, 2)], observations)
        self.assertEqual("commit", result.commit_event.operation)
        self.assertTrue(result.execution.succeeded)
        self.assertTrue(result.settled)
        self.assertEqual("settle", result.settlement_event.operation)
        self.assertEqual(1, result.settlement_event.details["spent"])
        self.assertEqual(1, result.settlement_event.details["released"])
        self.assertEqual(0, magic.committed_by("bdo"))
        self.assertEqual(2, magic.claimed_by("bdo", locality="network"))
        self.assertEqual(1, magic.spent_total(locality="network"))
        self.assertEqual(20, result.total_before)
        self.assertEqual(20, result.total_after)

    def test_commit_failure_occurs_before_executor(self):
        router = ConsequenceRouter()
        magic = MagicRuntime(
            20,
            limits(),
            initial_locality="network",
            access_resolver=lambda actor, operation, locality: operation != "mana.commit",
            consequence_verifier=router,
        )
        magic.claim("bdo", "network", 3)
        view, attachment = attached()
        calls = {"executor": 0}

        with self.assertRaisesRegex(MagicRuntimeError, "magic access unavailable: mana.commit"):
            run_mana_cast(
                attachment,
                view,
                magic,
                effect_probe=probe("effect"),
                mana_probe=probe("mana"),
                executor=lambda *_: calls.__setitem__("executor", calls["executor"] + 1),
            )

        self.assertEqual(0, calls["executor"])
        self.assertEqual(3, magic.claimed_by("bdo", locality="network"))
        self.assertEqual(0, magic.committed_by("bdo"))

    def test_failed_execution_still_settles_from_independent_consequence(self):
        router = ConsequenceRouter()
        magic = runtime(router)
        magic.claim("bdo", "network", 3)
        view, attachment = attached()

        def executor(_closed, cast_id):
            router.effects[cast_id] = 1
            raise RuntimeError("Technique failed after external consequence")

        result = run_mana_cast(
            attachment,
            view,
            magic,
            effect_probe=probe("effect"),
            mana_probe=probe("mana"),
            executor=executor,
        )

        self.assertFalse(result.execution.succeeded)
        self.assertEqual("RuntimeError", result.execution.error_type)
        self.assertTrue(result.settled)
        self.assertEqual(1, result.settlement_event.details["spent"])
        self.assertEqual(0, magic.committed_by("bdo"))
        self.assertEqual(1, magic.spent_total(locality="network"))

    def test_execution_success_does_not_decide_spending(self):
        router = ConsequenceRouter()
        magic = runtime(router)
        magic.claim("bdo", "network", 3)
        view, attachment = attached()

        result = run_mana_cast(
            attachment,
            view,
            magic,
            effect_probe=probe("effect"),
            mana_probe=probe("mana"),
            executor=lambda _closed, cast_id: router.effects.__setitem__(cast_id, 0) or "executor-success",
        )

        self.assertTrue(result.execution.succeeded)
        self.assertEqual(0, result.settlement_event.details["spent"])
        self.assertEqual(2, result.settlement_event.details["released"])
        self.assertEqual(3, magic.claimed_by("bdo", locality="network"))


class ReplayAndSettlementTests(unittest.TestCase):
    def test_same_closed_attempt_cannot_commit_or_execute_twice(self):
        router = ConsequenceRouter()
        magic = runtime(router)
        magic.claim("bdo", "network", 3)
        view, attachment = attached()
        calls = {"executor": 0}

        def executor(_closed, cast_id):
            calls["executor"] += 1
            router.effects[cast_id] = 0

        first = run_mana_cast(
            attachment,
            view,
            magic,
            effect_probe=probe("effect"),
            mana_probe=probe("mana"),
            executor=executor,
        )
        self.assertTrue(first.settled)

        with self.assertRaisesRegex(MagicRuntimeError, "cast id already used for Mana"):
            run_mana_cast(
                attachment,
                view,
                magic,
                effect_probe=probe("effect"),
                mana_probe=probe("mana"),
                executor=executor,
            )

        self.assertEqual(1, calls["executor"])
        self.assertEqual(1, sum(event.operation == "commit" for event in magic.events))
        self.assertEqual(1, sum(event.operation == "settle" for event in magic.events))

    def test_unavailable_consequence_leaves_commitment_for_settlement_only_retry(self):
        router = ConsequenceRouter()
        router.available = False
        magic = runtime(router)
        magic.claim("bdo", "network", 3)
        view, attachment = attached()
        calls = {"executor": 0}

        def executor(_closed, cast_id):
            calls["executor"] += 1
            router.effects[cast_id] = 1

        result = run_mana_cast(
            attachment,
            view,
            magic,
            effect_probe=probe("effect"),
            mana_probe=probe("mana"),
            executor=executor,
        )
        self.assertFalse(result.settled)
        self.assertIn("consequence observation unavailable", result.settlement_error)
        self.assertEqual(2, magic.committed_by("bdo"))
        self.assertEqual(1, calls["executor"])

        router.available = True
        event = settle_mana_cast(result.closed_plan, magic)
        self.assertEqual("settle", event.operation)
        self.assertEqual(1, calls["executor"])
        self.assertEqual(0, magic.committed_by("bdo"))

    def test_one_shared_magic_runtime_routes_distinct_consequences_by_cast_id(self):
        router = ConsequenceRouter()
        magic = runtime(router)
        magic.claim("bdo", "network", 6)
        results = []

        for attempt, observed_effect in (("first", 1), ("second", 2)):
            view, attachment = attached(attempt)

            def executor(_closed, cast_id, amount=observed_effect):
                router.effects[cast_id] = amount
                return amount

            results.append(
                run_mana_cast(
                    attachment,
                    view,
                    magic,
                    effect_probe=probe("effect"),
                    mana_probe=probe("mana"),
                    executor=executor,
                )
            )

        self.assertNotEqual(results[0].cast_id, results[1].cast_id)
        self.assertEqual([1, 2], [item.settlement_event.details["spent"] for item in results])
        self.assertEqual([item.cast_id for item in results], router.calls)
        self.assertEqual(20, magic.total())
        self.assertEqual(3, magic.spent_total(locality="network"))

    def test_mana_cast_id_is_derived_from_immutable_closed_plan(self):
        router = ConsequenceRouter()
        magic = runtime(router)
        magic.claim("bdo", "network", 3)
        view, attachment = attached()
        result = run_mana_cast(
            attachment,
            view,
            magic,
            effect_probe=probe("effect"),
            mana_probe=probe("mana"),
            executor=lambda _closed, cast_id: router.effects.__setitem__(cast_id, 0),
        )
        self.assertEqual(f"closed-plan:{result.closed_plan.digest}", result.cast_id)
        self.assertEqual(result.cast_id, mana_cast_id(result.closed_plan))


class BoundaryTests(unittest.TestCase):
    def test_integration_never_calls_magic_claim(self):
        tree = ast.parse(SEAM.read_text(encoding="utf-8"))
        called_attributes = [
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        ]
        self.assertNotIn("claim", called_attributes)

    def test_result_is_integration_evidence_not_cast_seal(self):
        router = ConsequenceRouter()
        magic = runtime(router)
        magic.claim("bdo", "network", 3)
        view, attachment = attached()
        result = run_mana_cast(
            attachment,
            view,
            magic,
            effect_probe=probe("effect"),
            mana_probe=probe("mana"),
            executor=lambda _closed, cast_id: router.effects.__setitem__(cast_id, 0),
        )
        self.assertFalse(hasattr(result, "cast_record"))
        self.assertFalse(hasattr(result, "seal"))
        self.assertEqual("commit", result.commit_event.operation)
        self.assertEqual("settle", result.settlement_event.operation)


if __name__ == "__main__":
    unittest.main()
