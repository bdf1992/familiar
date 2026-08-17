"""Evidenced Situation -> open CrossingPlan attachment specimens for issue #71."""

from __future__ import annotations

import ast
from copy import deepcopy
import json
from pathlib import Path
import unittest

from cast.practitioner.crossing import (
    CrossingPlan,
    EvidenceContract,
    ManaParticipation,
    ResidualBounds,
    canonical_material,
)
from cast.practitioner.handle_situation import (
    resolve_handle_situation,
    situation_evidence_digest,
)
from cast.practitioner.obligations import (
    CAPABILITY_GATE,
    STATE_PREDICATE,
    DischargeMechanism,
    RuntimeObligation,
)
from cast.practitioner.situation import CapabilityReceipt, Demand
from cast.practitioner.situation_crossing import (
    SituationCrossingError,
    construct_open_crossing_plan,
)
from familiar.domain_handle import resolve_domain_handle


ROOT = Path(__file__).resolve().parents[2]
HANDLE_FIXTURES = ROOT / "familiar" / "domain_handle" / "fixtures"
ENV_FIXTURE = ROOT / "cast" / "tests" / "fixtures" / "domain-handle-environment-69.json"
ATTACHMENT = ROOT / "cast" / "practitioner" / "situation_crossing.py"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def subject(subject_id: str, dialect: str, attention: str) -> dict:
    return {
        "familiar_format": "0.3",
        "id": f"{subject_id}.familiar",
        "caster": {"id": subject_id, "kind": "human"},
        "dialect": {"description": dialect},
        "attention": [attention],
        "preferences": ["small inspectable changes"],
        "stake": ["practitioner understanding"],
        "advisory_authority": ["presentation", "attention"],
    }


def handle(subject_familiar: dict | None = None) -> dict:
    return resolve_domain_handle(
        load_json(HANDLE_FIXTURES / "context.json"),
        load_json(HANDLE_FIXTURES / "domain-familiarity.json"),
        subject_familiar,
    )


def environment_fixture() -> dict:
    return load_json(ENV_FIXTURE)


def concrete_receipts(fixture: dict) -> tuple[CapabilityReceipt, ...]:
    values = []
    for raw in fixture["capability_receipts"]:
        item = deepcopy(raw)
        item["operations"] = tuple(item["operations"])
        values.append(CapabilityReceipt(**item))
    return tuple(values)


def repository_demand(required: tuple[str, ...] = ("contents:read",)) -> Demand:
    return Demand(
        operation="read",
        relation="permissions",
        capability="repository-read",
        environment="github",
        authority="read",
        subject="bdf1992/familiar",
        locator="bdf1992/familiar",
        capacity={"required": required},
        attenuate=True,
    )


def situation_intent() -> dict:
    return {
        "id": "prepare-repository-inspection",
        "situation": {
            "id": "situation:71",
            "session_id": "session:71",
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
            },
            {
                "id": "repository-anchor",
                "charted": {
                    "status": "present",
                    "path": ["context", "identity", "anchor"],
                },
                "observation": "repository-anchor",
                "compare_as": "anchor",
            },
            {
                "id": "live-practitioner-host-state",
                "charted": {
                    "status": "unknown",
                    "claim": "live practitioner host state is unobserved by this chart",
                },
                "observation": "live-practitioner-host-state",
                "compare_as": "identity",
            },
        ],
    }


def situation_view(
    subject_familiar: dict | None = None,
    fixture: dict | None = None,
    demand: Demand | None = None,
) -> dict:
    fixture = fixture or environment_fixture()
    demand = demand or repository_demand()
    return resolve_handle_situation(
        handle(subject_familiar),
        situation_intent(),
        fixture["observations"],
        concrete_receipts(fixture),
        {"repo-read-gate": demand},
    )


def obligations(demand: Demand | None = None) -> tuple[RuntimeObligation, ...]:
    demand = demand or repository_demand()
    return (
        RuntimeObligation(
            id="repo-read-gate",
            requirement_id="repository-readable",
            kind=CAPABILITY_GATE,
            phase="before",
            demand=demand,
            spec={"purpose": "inspect exact repository contents"},
        ),
        RuntimeObligation(
            id="target-shape",
            requirement_id="target-is-repository",
            kind=STATE_PREDICATE,
            phase="before",
            spec={"expected": "repository"},
        ),
    )


def mechanisms() -> tuple[DischargeMechanism, ...]:
    return (
        DischargeMechanism(
            id="repository-target-check",
            kind=STATE_PREDICATE,
            provenance="test:independent-target-check",
            evidence_contract="target has repository identity",
            check=lambda obligation, context: bool(context.get("target")),
        ),
    )


def mana() -> tuple[ManaParticipation, ...]:
    return (
        ManaParticipation(
            locality="local:test",
            participant="agent:test",
            claim=4,
            commit=2,
        ),
    )


def evidence_contracts() -> tuple[EvidenceContract, ...]:
    return (
        EvidenceContract(
            obligation_id="repo-read-gate",
            contract="exact capability matcher evidence",
            observer="cast:capability-matcher",
        ),
        EvidenceContract(
            obligation_id="target-shape",
            contract="independent repository target predicate",
            observer="test:independent-target-check",
        ),
    )


def construct(view: dict, *, obligation_values=None) -> CrossingPlan:
    return construct_open_crossing_plan(
        view,
        spell={"id": "spell:inspect-repository", "effect": "inspect"},
        technique={"id": "technique:github-read", "operation": "read"},
        obligations=obligation_values or obligations(),
        mechanisms=mechanisms(),
        mana=mana(),
        evidence_contracts=evidence_contracts(),
        residual_bounds=ResidualBounds(("read-log",)),
        required_situation_evidence=("environment-domain-role",),
    )


class AttachmentTests(unittest.TestCase):
    def test_end_to_end_specimen_constructs_a_ready_open_crossing_plan(self):
        view = situation_view(subject("bdo", "compact", "runtime boundaries"))
        plan = construct(view)

        self.assertIsInstance(plan, CrossingPlan)
        self.assertTrue(plan.ready)
        self.assertFalse(hasattr(plan, "digest"))
        self.assertEqual(view["situation_evidence_digest"], plan.configuration["situation_evidence"]["digest"])
        self.assertEqual(
            {"repository": "bdf1992/familiar"}, plan.configuration["target"]
        )
        self.assertEqual("technique:github-read", plan.configuration["technique"]["id"])

    def test_exact_situation_receipt_and_attenuated_handle_become_plan_capacity(self):
        view = situation_view()
        plan = construct(view)
        match = plan.capacity.matches["repo-read-gate"]
        recorded = view["capability_matching"]["matches"]["repo-read-gate"]

        self.assertEqual(recorded["receipt"]["evidence"], match.receipt.evidence)
        self.assertEqual(recorded["receipt"]["capacity"], dict(match.receipt.capacity))
        self.assertEqual(recorded["handle"]["capacity"], dict(match.handle.capacity))
        self.assertTrue(match.attenuated)

    def test_changed_environment_receipt_changes_situation_and_plan_evidence(self):
        original_view = situation_view()
        changed_fixture = environment_fixture()
        changed_fixture["capability_receipts"][0]["evidence"] = "github-connector:replacement-receipt"
        changed_view = situation_view(fixture=changed_fixture)

        original = construct(original_view)
        changed = construct(changed_view)

        self.assertNotEqual(
            original.configuration["situation_evidence"]["digest"],
            changed.configuration["situation_evidence"]["digest"],
        )
        self.assertNotEqual(
            original.capacity.matches["repo-read-gate"].receipt.evidence,
            changed.capacity.matches["repo-read-gate"].receipt.evidence,
        )

    def test_stale_digest_refuses_tampered_situation_match(self):
        view = situation_view()
        view["capability_matching"]["matches"]["repo-read-gate"]["receipt"]["evidence"] = "forged"

        with self.assertRaisesRegex(SituationCrossingError, "digest does not match"):
            construct(view)

    def test_recomputed_digest_still_cannot_hide_binding_tamper(self):
        view = situation_view()
        view["capability_matching"]["matches"]["repo-read-gate"]["receipt"]["evidence"] = "forged"
        view["situation_evidence_digest"] = situation_evidence_digest(view)

        with self.assertRaisesRegex(SituationCrossingError, "does not match evidenced Situation binding"):
            construct(view)

    def test_a_different_demand_cannot_reuse_the_same_recorded_binding(self):
        view = situation_view()
        widened = repository_demand(("contents:read", "metadata:read"))

        with self.assertRaisesRegex(SituationCrossingError, "does not match evidenced Situation binding"):
            construct(view, obligation_values=obligations(widened))

    def test_two_subject_familiars_have_same_situated_identity_and_plan_material(self):
        software = situation_view(subject("software", "software terminology", "permissions"))
        magic = situation_view(subject("magic", "magic terminology", "spell boundaries"))

        self.assertNotEqual(software["handle_projection"], magic["handle_projection"])
        self.assertEqual(software["situation_evidence_digest"], magic["situation_evidence_digest"])
        self.assertEqual(canonical_material(construct(software)), canonical_material(construct(magic)))

    def test_required_unobservable_situation_evidence_fails_closed(self):
        view = situation_view()
        with self.assertRaisesRegex(SituationCrossingError, "required Situation evidence is unresolved"):
            construct_open_crossing_plan(
                view,
                spell={"id": "spell:inspect-repository"},
                technique={"id": "technique:github-read"},
                obligations=obligations(),
                mechanisms=mechanisms(),
                mana=mana(),
                evidence_contracts=evidence_contracts(),
                residual_bounds=ResidualBounds(("read-log",)),
                required_situation_evidence=("live-practitioner-host-state",),
            )

    def test_situation_capability_gap_is_not_permission(self):
        fixture = environment_fixture()
        view = resolve_handle_situation(
            handle(),
            situation_intent(),
            fixture["observations"],
            (),
            {"repo-read-gate": repository_demand()},
        )
        self.assertFalse(view["capability_matching"]["ready"])

        with self.assertRaisesRegex(SituationCrossingError, "not ready"):
            construct(view)

    def test_three_algebras_and_evidence_contracts_stay_separately_inspectable(self):
        plan = construct(situation_view())

        self.assertEqual({"repo-read-gate", "target-shape"}, set(plan.obligations.bindings))
        self.assertEqual({"repo-read-gate"}, set(plan.capacity.matches))
        self.assertEqual(4, plan.mana[0].claim)
        self.assertEqual(2, plan.mana[0].commit)
        self.assertEqual(2, len(plan.evidence_contracts))
        self.assertEqual(("read-log",), plan.residual_bounds.permitted)

    def test_existing_drift_and_uncertainty_are_carried_not_erased(self):
        view = situation_view()
        plan = construct(view)
        evidence = plan.configuration["situation_evidence"]

        self.assertIn(
            {"id": "repository-anchor", "result": "stale-anchor"}, evidence["drift"]
        )
        self.assertIn(
            {"id": "live-practitioner-host-state", "result": "unobservable"},
            evidence["uncertain"],
        )


class BoundaryTests(unittest.TestCase):
    def test_attachment_imports_no_closure_execution_magic_or_environment_path(self):
        tree = ast.parse(ATTACHMENT.read_text(encoding="utf-8"))
        imported_names: list[str] = []
        called_names: list[str] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_names.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_names.append(node.module)
                imported_names.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    called_names.append(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    called_names.append(node.func.attr)

        forbidden_import_parts = {"environment", "magic", "spell_kernel"}
        self.assertFalse(
            any(
                any(part in forbidden_import_parts for part in name.split("."))
                for name in imported_names
            )
        )
        for forbidden_call in ("close", "observe_brink", "plan_digest", "discharge"):
            self.assertNotIn(forbidden_call, called_names)

    def test_constructing_does_not_create_closed_plan_or_cast_record(self):
        plan = construct(situation_view())
        self.assertEqual("0.7-draft", canonical_material(plan)["crossing_plan_version"])
        self.assertNotIn("digest", plan.__dict__)
        self.assertNotIn("brink", plan.__dict__)
        self.assertNotIn("outcome", plan.__dict__)
        self.assertNotIn("cast", plan.__dict__)


if __name__ == "__main__":
    unittest.main()
