"""Observed Brink -> Closure specimens for issue #73."""

from __future__ import annotations

import ast
from copy import deepcopy
import json
from pathlib import Path
import unittest

from cast.practitioner.brink_closure import (
    BrinkClosureError,
    EnvironmentBrinkProbe,
    construct_attached_open_plan,
    observe_and_close,
)
from cast.practitioner.crossing import (
    CrossingPlanError,
    EvidenceContract,
    ManaParticipation,
    ResidualBounds,
    digest_matches,
    verify,
)
from cast.practitioner.handle_situation import resolve_handle_situation
from cast.practitioner.obligations import CAPABILITY_GATE, RuntimeObligation
from cast.practitioner.situation import CapabilityReceipt, Demand
from familiar.domain_handle import resolve_domain_handle


ROOT = Path(__file__).resolve().parents[2]
HANDLE_FIXTURES = ROOT / "familiar" / "domain_handle" / "fixtures"
ENV_FIXTURE = ROOT / "cast" / "tests" / "fixtures" / "domain-handle-environment-69.json"
SEAM = ROOT / "cast" / "practitioner" / "brink_closure.py"


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


def intent() -> dict:
    return {
        "id": "prepare-brink",
        "situation": {
            "id": "situation:73",
            "session_id": "session:73",
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
        ],
    }


def situation_view(subject_familiar: dict | None = None) -> dict:
    data = fixture()
    return resolve_handle_situation(
        handle(subject_familiar),
        intent(),
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


def attachment(subject_familiar: dict | None = None):
    view = situation_view(subject_familiar)
    attached = construct_attached_open_plan(
        view,
        spell={"id": "spell:inspect-repository", "effect": "inspect"},
        technique={"id": "technique:github-read", "operation": "read"},
        obligations=(obligation(),),
        mana=(
            ManaParticipation(
                locality="local:test",
                participant="agent:test",
                claim=4,
                commit=2,
            ),
        ),
        evidence_contracts=(
            EvidenceContract(
                obligation_id="repo-read-gate",
                contract="exact capability matcher evidence",
                observer="cast:capability-matcher",
            ),
        ),
        residual_bounds=ResidualBounds(("read-log",)),
        required_situation_evidence=("environment-domain-role",),
    )
    return view, attached


def probe(kind: str, value=0, *, observer: str | None = None, read=None):
    return EnvironmentBrinkProbe(
        kind=kind,
        environment="github",
        observer=observer or f"environment:{kind}-observer",
        provenance=f"probe:{kind}:independent",
        read=(lambda: value) if read is None else read,
    )


def close_clean(subject_familiar: dict | None = None):
    view, attached = attachment(subject_familiar)
    closed = observe_and_close(
        attached,
        view,
        effect_probe=probe("effect"),
        mana_probe=probe("mana"),
    )
    return view, attached, closed


class BrinkObservationTests(unittest.TestCase):
    def test_end_to_end_observes_brink_and_closes_exact_open_plan(self):
        view, attached, closed = close_clean()

        self.assertEqual(attached.plan, closed.plan)
        self.assertTrue(closed.brink.at_brink)
        self.assertEqual(0, closed.brink.effect_delta)
        self.assertEqual(0, closed.brink.mana_delta)
        self.assertTrue(closed.digest.startswith("sha256:"))
        self.assertNotEqual(attached.construction_digest, closed.digest)
        self.assertEqual(view["situation_evidence_digest"], attached.situation_evidence_digest)

        by_kind = {item["probe"]: item for item in closed.brink.observations}
        self.assertEqual("environment:effect-observer", by_kind["effect"]["observer"])
        self.assertEqual("probe:effect:independent", by_kind["effect"]["provenance"])
        self.assertEqual("environment:mana-observer", by_kind["mana"]["observer"])
        self.assertEqual("github", by_kind["mana"]["environment"])

    def test_missing_effect_probe_is_unobservable_and_refuses_closure(self):
        view, attached = attachment()
        with self.assertRaisesRegex(CrossingPlanError, "brink-unobservable: effect"):
            observe_and_close(
                attached,
                view,
                effect_probe=None,
                mana_probe=probe("mana"),
            )

    def test_missing_mana_probe_is_unobservable_and_refuses_closure(self):
        view, attached = attachment()
        with self.assertRaisesRegex(CrossingPlanError, "brink-unobservable: mana"):
            observe_and_close(
                attached,
                view,
                effect_probe=probe("effect"),
                mana_probe=None,
            )

    def test_raising_probes_are_unobservable_not_zero(self):
        def fail():
            raise RuntimeError("observer offline")

        for kind in ("effect", "mana"):
            with self.subTest(kind=kind):
                view, attached = attachment()
                kwargs = {
                    "effect_probe": probe("effect"),
                    "mana_probe": probe("mana"),
                }
                kwargs[f"{kind}_probe"] = probe(kind, read=fail)
                with self.assertRaisesRegex(CrossingPlanError, f"brink-unobservable: {kind}"):
                    observe_and_close(attached, view, **kwargs)

    def test_nonzero_cast_effect_refuses_closure(self):
        view, attached = attachment()
        with self.assertRaisesRegex(CrossingPlanError, "brink-effect-already-applied: 1"):
            observe_and_close(
                attached,
                view,
                effect_probe=probe("effect", 1),
                mana_probe=probe("mana", 0),
            )

    def test_nonzero_cast_mana_commitment_refuses_closure(self):
        view, attached = attachment()
        with self.assertRaisesRegex(CrossingPlanError, "brink-mana-already-committed: 2"):
            observe_and_close(
                attached,
                view,
                effect_probe=probe("effect", 0),
                mana_probe=probe("mana", 2),
            )

    def test_unrelated_environment_activity_does_not_block_cast_attributable_zero(self):
        environment_state = {
            "other_effects": 900,
            "other_committed_mana": 41,
            "this_cast_effects": 0,
            "this_cast_committed_mana": 0,
        }
        view, attached = attachment()
        closed = observe_and_close(
            attached,
            view,
            effect_probe=probe("effect", read=lambda: environment_state["this_cast_effects"]),
            mana_probe=probe("mana", read=lambda: environment_state["this_cast_committed_mana"]),
        )

        self.assertTrue(closed.brink.at_brink)
        self.assertEqual(900, environment_state["other_effects"])
        self.assertEqual(41, environment_state["other_committed_mana"])

    def test_caster_or_technique_cannot_supply_brink_observation(self):
        cases = (
            ("effect", "agent:test"),
            ("mana", "technique:github-read"),
        )
        for kind, observer in cases:
            with self.subTest(kind=kind, observer=observer):
                view, attached = attachment()
                kwargs = {
                    "effect_probe": probe("effect"),
                    "mana_probe": probe("mana"),
                }
                kwargs[f"{kind}_probe"] = probe(kind, observer=observer)
                with self.assertRaisesRegex(BrinkClosureError, "not independent"):
                    observe_and_close(attached, view, **kwargs)


class PreClosureAttachmentTests(unittest.TestCase):
    def test_every_material_plan_mutation_is_detected_before_sealing(self):
        def mutate_target(attached):
            attached.plan.configuration["target"]["repository"] = "other/repo"

        def mutate_situation_digest(attached):
            attached.plan.configuration["situation_evidence"]["digest"] = "sha256:forged"

        def mutate_receipt(attached):
            match = attached.plan.capacity.matches["repo-read-gate"]
            object.__setattr__(match.receipt, "evidence", "forged-receipt")

        def mutate_handle(attached):
            match = attached.plan.capacity.matches["repo-read-gate"]
            match.handle.capacity["granted"] = ("contents:read", "metadata:read")

        def mutate_demand(attached):
            match = attached.plan.capacity.matches["repo-read-gate"]
            match.demand.capacity["required"] = ("contents:read", "metadata:read")

        def mutate_authority(attached):
            match = attached.plan.capacity.matches["repo-read-gate"]
            object.__setattr__(match.receipt, "authority", "admin")

        def mutate_obligation(attached):
            binding = attached.plan.obligations.bindings["repo-read-gate"]
            binding.obligation.spec["purpose"] = "broadened after construction"

        def mutate_evidence_contract(attached):
            object.__setattr__(attached.plan.evidence_contracts[0], "observer", "technique:self")

        def mutate_residual_bound(attached):
            object.__setattr__(attached.plan.residual_bounds, "permitted", ("anything",))

        def mutate_technique(attached):
            attached.plan.configuration["technique"]["id"] = "technique:other"

        def mutate_mana(attached):
            object.__setattr__(attached.plan.mana[0], "commit", 3)

        mutations = {
            "target": mutate_target,
            "Situation digest": mutate_situation_digest,
            "receipt": mutate_receipt,
            "attenuated handle": mutate_handle,
            "Demand": mutate_demand,
            "authority": mutate_authority,
            "obligation": mutate_obligation,
            "evidence contract": mutate_evidence_contract,
            "residual bound": mutate_residual_bound,
            "Technique": mutate_technique,
            "Mana": mutate_mana,
        }

        for name, mutate in mutations.items():
            with self.subTest(name=name):
                view, attached = attachment()
                mutate(attached)
                with self.assertRaisesRegex(BrinkClosureError, "construction digest"):
                    observe_and_close(
                        attached,
                        view,
                        effect_probe=probe("effect"),
                        mana_probe=probe("mana"),
                    )

    def test_situation_mutation_even_with_recomputed_digest_breaks_attachment(self):
        view, attached = attachment()
        view["situation"]["target"] = {"repository": "other/repo"}
        from cast.practitioner.handle_situation import situation_evidence_digest

        view["situation_evidence_digest"] = situation_evidence_digest(view)
        with self.assertRaisesRegex(BrinkClosureError, "different Situation evidence"):
            observe_and_close(
                attached,
                view,
                effect_probe=probe("effect"),
                mana_probe=probe("mana"),
            )

    def test_probe_cannot_mutate_plan_during_observation_and_then_close_it(self):
        view, attached = attachment()

        def mutating_probe():
            attached.plan.configuration["target"]["repository"] = "other/repo"
            return 0

        with self.assertRaisesRegex(BrinkClosureError, "construction digest"):
            observe_and_close(
                attached,
                view,
                effect_probe=probe("effect", read=mutating_probe),
                mana_probe=probe("mana"),
            )

    def test_two_subject_familiars_close_to_same_plan_identity(self):
        _, _, software = close_clean(
            subject("software", "software terminology", "permissions")
        )
        _, _, magic = close_clean(
            subject("magic", "magic terminology", "spell boundaries")
        )

        self.assertEqual(software.digest, magic.digest)
        self.assertEqual(software.material(), magic.material())

    def test_post_closure_mutation_is_detected_by_existing_verification(self):
        _, attached, closed = close_clean()
        attached.plan.configuration["target"]["repository"] = "other/repo"

        self.assertFalse(digest_matches(closed, attached.plan))
        violations = verify(closed, attached.plan)
        self.assertTrue(violations)
        self.assertTrue(any("configuration.target.repository" in item.path for item in violations))


class NoExecutionBoundaryTests(unittest.TestCase):
    def test_closure_moves_no_mana_and_executes_no_technique(self):
        mana_state = {"claimed": 4, "committed": 0, "spent": 0}
        technique_state = {"calls": 0}
        before_mana = deepcopy(mana_state)
        before_technique = deepcopy(technique_state)

        view, attached = attachment()
        closed = observe_and_close(
            attached,
            view,
            effect_probe=probe("effect", read=lambda: technique_state["calls"]),
            mana_probe=probe("mana", read=lambda: mana_state["committed"]),
        )

        self.assertTrue(closed.brink.at_brink)
        self.assertEqual(before_mana, mana_state)
        self.assertEqual(before_technique, technique_state)

    def test_seam_imports_no_magic_kernel_execution_or_cast_sealing_path(self):
        tree = ast.parse(SEAM.read_text(encoding="utf-8"))
        imports: list[str] = []
        called: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    called.append(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    called.append(node.func.attr)

        forbidden_import_parts = {"environment", "magic", "spell_kernel", "consequence"}
        self.assertFalse(
            any(
                any(part in forbidden_import_parts for part in name.split("."))
                for name in imports
            )
        )
        for forbidden_call in ("commit", "settle", "execute", "cast", "seal"):
            self.assertNotIn(forbidden_call, called)


if __name__ == "__main__":
    unittest.main()
