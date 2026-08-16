"""Read-only HandleView -> Situation evidence specimens for issue #69."""

from __future__ import annotations

import ast
from copy import deepcopy
import json
from pathlib import Path
import unittest

from cast.practitioner.handle_situation import HandleSituationError, resolve_handle_situation
from cast.practitioner.situation import CapabilityReceipt, Demand
from familiar.domain_handle import resolve_domain_handle


ROOT = Path(__file__).resolve().parents[2]
HANDLE_FIXTURES = ROOT / "familiar" / "domain_handle" / "fixtures"
ENV_FIXTURE = ROOT / "cast" / "tests" / "fixtures" / "domain-handle-environment-69.json"
SEAM = ROOT / "cast" / "practitioner" / "handle_situation.py"


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
    context = load_json(HANDLE_FIXTURES / "context.json")
    familiar = load_json(HANDLE_FIXTURES / "domain-familiarity.json")
    return resolve_domain_handle(context, familiar, subject_familiar)


def environment_fixture() -> dict:
    return load_json(ENV_FIXTURE)


def receipts(fixture: dict) -> tuple[CapabilityReceipt, ...]:
    values = []
    for raw in fixture["capability_receipts"]:
        item = deepcopy(raw)
        item["operations"] = tuple(item["operations"])
        values.append(CapabilityReceipt(**item))
    return tuple(values)


def intent() -> dict:
    return {
        "id": "orient-to-familiar-repository",
        "situation": {
            "id": "situation:69",
            "session_id": "session:69",
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


def requirements() -> dict[str, Demand]:
    return {
        "inspect-repository": Demand(
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
    }


class SituationEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = environment_fixture()
        self.handle = handle(subject("bdo", "compact", "runtime boundaries"))

    def resolve(self, **overrides):
        return resolve_handle_situation(
            overrides.get("handle_view", self.handle),
            overrides.get("intent_value", intent()),
            overrides.get("observations", self.fixture["observations"]),
            overrides.get("receipts_value", receipts(self.fixture)),
            overrides.get("requirements_value", requirements()),
        )

    def test_one_charted_claim_is_confirmed_by_exact_environment_evidence(self):
        view = self.resolve()
        comparison = next(
            item for item in view["comparisons"] if item["id"] == "environment-domain-role"
        )

        self.assertEqual("confirmed", comparison["result"])
        self.assertEqual(
            "repo:environment/README.md@003ca4815a491679e9ecf88511cb5abadcd1241f",
            comparison["runtime"]["evidence"],
        )

    def test_stale_context_anchor_is_drift_not_silent_reconciliation(self):
        view = self.resolve()
        finding = next(item for item in view["drift"] if item["id"] == "repository-anchor")

        self.assertEqual("stale-anchor", finding["result"])
        self.assertEqual(
            "b3518f70e674501e29f241376400fcd3a972ae1b",
            finding["charted"]["value"],
        )
        self.assertEqual(
            "003ca4815a491679e9ecf88511cb5abadcd1241f",
            finding["runtime"]["value"],
        )

    def test_unobservable_state_remains_unknown_not_absent(self):
        view = self.resolve()
        finding = next(
            item for item in view["uncertain"]
            if item["id"] == "live-practitioner-host-state"
        )

        self.assertEqual("unobservable", finding["result"])
        self.assertEqual("unknown", finding["charted"]["status"])
        self.assertEqual("unobservable", finding["runtime"]["status"])

    def test_missing_chart_path_cannot_be_inferred_as_absence(self):
        bad_intent = intent()
        bad_intent["expectations"] = [
            {
                "id": "invented-absence",
                "charted": {"status": "present", "path": ["context", "does-not-exist"]},
                "observation": "environment-domain-role",
            }
        ]
        with self.assertRaisesRegex(HandleSituationError, "not absence"):
            self.resolve(intent_value=bad_intent)

    def test_concrete_capability_matching_reuses_existing_demand_logic(self):
        view = self.resolve()
        match = view["capability_matching"]["matches"]["inspect-repository"]

        self.assertTrue(view["capability_matching"]["ready"])
        self.assertEqual([], view["capability_matching"]["gaps"])
        self.assertEqual(
            "github-connector:contents-read@003ca4815a491679e9ecf88511cb5abadcd1241f",
            match["receipt"]["evidence"],
        )
        self.assertEqual(
            ["contents:read", "metadata:read"], match["receipt"]["capacity"]["granted"]
        )
        self.assertEqual(["contents:read"], match["handle"]["capacity"]["granted"])
        self.assertTrue(match["attenuated"])

    def test_observation_prose_never_becomes_a_capability_receipt(self):
        observations = deepcopy(self.fixture["observations"])
        observations["imagined-capability"] = {
            "status": "present",
            "value": {"operation": "read", "authority": "all"},
            "evidence": "chart-prose:not-a-receipt",
        }
        view = self.resolve(observations=observations, receipts_value=())

        self.assertFalse(view["capability_matching"]["ready"])
        self.assertEqual(
            ["capability-missing:inspect-repository:read"],
            view["capability_matching"]["gaps"],
        )
        self.assertEqual([], view["environment"]["capability_receipts"])

    def test_two_subject_familiars_cannot_change_receipt_matching(self):
        software = self.resolve(
            handle_view=handle(subject("software", "software terminology", "permissions"))
        )
        magic = self.resolve(
            handle_view=handle(subject("magic", "magic terminology", "spell boundaries"))
        )

        self.assertNotEqual(software["handle_projection"], magic["handle_projection"])
        self.assertEqual(software["environment"], magic["environment"])
        self.assertEqual(software["capability_matching"], magic["capability_matching"])

    def test_explicit_drift_kinds_remain_distinct(self):
        synthetic = deepcopy(self.handle)
        synthetic["context"]["runtime_expectations"] = {
            "identity": "mechanism:v1",
            "capacity": 5,
        }
        observations = deepcopy(self.fixture["observations"])
        observations.update(
            {
                "mechanism-identity": {
                    "status": "present",
                    "value": "mechanism:v2",
                    "evidence": "probe:identity:v2",
                },
                "mechanism-capacity": {
                    "status": "present",
                    "value": 3,
                    "evidence": "probe:capacity:3",
                },
                "unexpected-mechanism": {
                    "status": "present",
                    "value": "mechanism:new",
                    "evidence": "probe:unexpected:new",
                },
            }
        )
        synthetic_intent = intent()
        synthetic_intent["expectations"] = [
            {
                "id": "identity-change",
                "charted": {
                    "status": "present",
                    "path": ["context", "runtime_expectations", "identity"],
                },
                "observation": "mechanism-identity",
                "compare_as": "identity",
            },
            {
                "id": "capacity-change",
                "charted": {
                    "status": "present",
                    "path": ["context", "runtime_expectations", "capacity"],
                },
                "observation": "mechanism-capacity",
                "compare_as": "capacity",
            },
            {
                "id": "explicit-absence-defeated",
                "charted": {
                    "status": "absent",
                    "claim": "this bounded chart explicitly recorded no such mechanism",
                },
                "observation": "unexpected-mechanism",
                "compare_as": "identity",
            },
        ]

        view = self.resolve(handle_view=synthetic, intent_value=synthetic_intent, observations=observations)
        kinds = {item["result"] for item in view["drift"]}
        self.assertEqual(
            {"changed-identity", "changed-capacity", "charted-absent/runtime-present"},
            kinds,
        )

    def test_output_is_copy_isolated_and_explicitly_non_effectful(self):
        original_handle = deepcopy(self.handle)
        original_observations = deepcopy(self.fixture["observations"])
        view = self.resolve()

        view["handle_sources"]["context"]["anchor"] = "mutated"
        view["environment"]["observations"]["repository-anchor"]["value"] = "mutated"

        self.assertEqual(original_handle, self.handle)
        self.assertEqual(original_observations, self.fixture["observations"])
        self.assertFalse(view["effectful"])
        self.assertEqual([], view["runtime_authority"])
        self.assertEqual(["inspect", "orient", "prepare-situation"], view["affordances"])


class BoundaryTests(unittest.TestCase):
    def test_seam_has_no_closure_magic_kernel_or_environment_import(self):
        tree = ast.parse(SEAM.read_text(encoding="utf-8"))
        imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)

        forbidden = ("crossing", "magic", "kernel", "environment")
        self.assertFalse(any(any(part in name.split(".") for part in forbidden) for name in imports))


if __name__ == "__main__":
    unittest.main()
