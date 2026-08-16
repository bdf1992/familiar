"""Read-only Domain Handle specimens for issue #67.

These tests pin the smallest useful claim: Context, Domain Familiarity, and an
optional Subject Familiar can be composed for inspection without flattening
source identity or creating an effectful path.
"""

from __future__ import annotations

import ast
from copy import deepcopy
import json
from pathlib import Path
import unittest

from familiar.domain_handle import DomainHandleError, resolve_domain_handle


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "familiar" / "domain_handle" / "fixtures"
RESOLVER = ROOT / "familiar" / "domain_handle" / "resolver.py"


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


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


class DomainHandleResolutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.context = load("context.json")
        self.domain_familiar = load("domain-familiarity.json")

    def test_sources_remain_separately_addressable_with_exact_content_identity(self):
        view = resolve_domain_handle(self.context, self.domain_familiar)

        self.assertEqual(self.context, view["context"])
        self.assertEqual(self.domain_familiar, view["domain_familiarity"])
        self.assertNotEqual(
            view["sources"]["context"]["digest"],
            view["sources"]["domain_familiarity"]["digest"],
        )
        self.assertEqual(
            self.context["identity"]["anchor"], view["sources"]["context"]["anchor"]
        )
        self.assertEqual(
            self.domain_familiar["identity"]["anchor"],
            view["sources"]["domain_familiarity"]["anchor"],
        )

    def test_real_repository_disagreement_survives_resolution(self):
        view = resolve_domain_handle(self.context, self.domain_familiar)

        finding = next(
            item for item in view["disagreements"]
            if item["id"] == "readme-crossing-plan-staleness"
        )
        self.assertIn("README", finding["older"])
        self.assertIn("PR #63", finding["newer"])
        self.assertIn("runtime attachment", finding["interpretation"])

    def test_unknown_and_unobserved_are_preserved_not_converted_to_absence(self):
        view = resolve_domain_handle(self.context, self.domain_familiar)

        self.assertEqual(self.context["unknown"], view["unknown"])
        self.assertEqual(self.context["unobserved"], view["unobserved"])
        self.assertIn("live practitioner host state", view["unobserved"])

    def test_two_subjects_change_projection_without_changing_domain_sources(self):
        software = resolve_domain_handle(
            self.context,
            self.domain_familiar,
            subject("software-user", "software terminology", "runtime boundaries"),
        )
        magic = resolve_domain_handle(
            self.context,
            self.domain_familiar,
            subject("magic-user", "magic terminology", "spell semantics"),
        )

        self.assertNotEqual(software["projection"]["subject"], magic["projection"]["subject"])
        self.assertEqual(software["sources"], magic["sources"])
        self.assertEqual(software["context"], magic["context"])
        self.assertEqual(software["domain_familiarity"], magic["domain_familiarity"])

    def test_subject_advisory_authority_never_becomes_runtime_authority(self):
        view = resolve_domain_handle(
            self.context,
            self.domain_familiar,
            subject("bdo", "compact", "crossings"),
        )

        self.assertEqual(["presentation", "attention"], view["projection"]["subject"]["advisory_authority"])
        self.assertEqual([], view["projection"]["subject"]["runtime_authority"])
        self.assertEqual([], view["runtime_authority"])

    def test_output_is_copy_isolated_from_all_inputs(self):
        original_context = deepcopy(self.context)
        original_familiar = deepcopy(self.domain_familiar)
        subj = subject("bdo", "compact", "crossings")
        original_subject = deepcopy(subj)

        view = resolve_domain_handle(self.context, self.domain_familiar, subj)
        view["context"]["unknown"].append("consumer mutation")
        view["domain_familiarity"]["heuristics"].append({"claim": "consumer mutation"})
        view["projection"]["subject"]["attention"].append("consumer mutation")

        self.assertEqual(original_context, self.context)
        self.assertEqual(original_familiar, self.domain_familiar)
        self.assertEqual(original_subject, subj)

    def test_anchor_mismatch_fails_closed(self):
        other = deepcopy(self.domain_familiar)
        other["identity"]["anchor"] = "different-commit"
        with self.assertRaisesRegex(DomainHandleError, "same anchor"):
            resolve_domain_handle(self.context, other)


class ReadOnlyBoundaryTests(unittest.TestCase):
    def test_resolver_has_no_cast_or_environment_import(self):
        tree = ast.parse(RESOLVER.read_text(encoding="utf-8"))
        imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)

        self.assertFalse(any(name == "cast" or name.startswith("cast.") for name in imports))
        self.assertFalse(
            any(name == "environment" or name.startswith("environment.") for name in imports)
        )

    def test_resolved_surface_is_explicitly_non_effectful(self):
        view = resolve_domain_handle(load("context.json"), load("domain-familiarity.json"))

        self.assertFalse(view["effectful"])
        self.assertEqual(["inspect", "orient"], view["affordances"])
        self.assertEqual([], view["runtime_authority"])


if __name__ == "__main__":
    unittest.main()
