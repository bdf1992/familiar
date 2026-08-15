import json
import unittest
from pathlib import Path

from runtime.spell_runtime import evaluate_trials, validate_cast, validate_definition


ROOT = Path(__file__).resolve().parents[1]


def load_familiar():
    with (ROOT / "spells" / "familiar" / "SPELL.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)


def valid_cast(spell):
    return {
        "cast_id": "cast-001",
        "spell": {
            "id": spell["identity"]["id"],
            "version": spell["identity"]["version"],
        },
        "caster": {"id": "holder-1", "kind": "human"},
        "familiars": [{"id": "owl.system", "role": "system", "stake": "familiar-making"}],
        "target": {"holder": "holder-1"},
        "intent": "Register the holder-recognized Familiar",
        "expression": "register",
        "inputs": {},
        "telemetry": [
            {
                "id": "holder_context",
                "value": {"holder": "holder-1", "scope": "primary"},
                "source": {"kind": "user-input"},
                "freshness_ms": 0,
            },
            {
                "id": "holder_authority",
                "value": {"can_adopt": True},
                "source": {"kind": "user-input"},
                "freshness_ms": 0,
            },
        ],
        "requirements": [
            {"id": "holder-resolved", "status": "satisfied"},
            {"id": "evidence-attributed", "status": "satisfied"},
        ],
        "limits": [
            {"id": "holder-controls-form", "status": "satisfied"},
            {"id": "candidate-before-recognition", "status": "satisfied"},
            {"id": "metaphor-yields-to-reality", "status": "satisfied"},
            {"id": "stake-bounds-reach", "status": "satisfied"},
        ],
        "energy": {
            "available": {"holder-participation": "interactive"},
            "committed": {"holder-participation": "recognition"},
        },
        "expected_effect": {"kind": "registered-familiar"},
        "actual_effect": {"kind": "registered-familiar", "form": "owl"},
        "evidence": [
            {
                "id": "effect-record",
                "kind": "registration",
                "summary": "holder-recognized Familiar registration",
            }
        ],
        "residuals": [],
        "status": "resolved",
    }


class DefinitionTests(unittest.TestCase):
    def test_familiar_definition_is_semantically_valid(self):
        self.assertEqual([], validate_definition(load_familiar()))

    def test_duplicate_expression_is_rejected(self):
        spell = load_familiar()
        spell["invocation"]["expressions"].append(dict(spell["invocation"]["expressions"][0]))
        issues = validate_definition(spell)
        self.assertTrue(any(issue.code == "duplicate-expression" for issue in issues))


class StandingTests(unittest.TestCase):
    def test_effect_only_is_practiced_trick(self):
        standing = evaluate_trials([
            {"id": "works", "passed": True, "proves": ["effect"]},
        ])
        self.assertEqual("trick", standing.kind)
        self.assertEqual("practiced", standing.trick)
        self.assertIn("telemetry-sensitive", standing.missing_proofs)

    def test_level_zero_requires_governance_not_just_effect(self):
        standing = evaluate_trials([
            {
                "id": "all-minimum-proofs",
                "passed": True,
                "proves": [
                    "effect",
                    "telemetry-sensitive",
                    "requirements",
                    "limits",
                    "evidence",
                ],
            }
        ])
        self.assertEqual("spell", standing.kind)
        self.assertEqual(0, standing.demonstrated_level)

    def test_claimed_level_does_not_change_demonstrated_standing(self):
        spell = load_familiar()
        spell["evaluation"]["claimed_level"] = 9
        self.assertEqual([], validate_definition(spell))
        standing = evaluate_trials([{"id": "nice-effect", "passed": True, "proves": ["effect"]}])
        self.assertEqual("trick", standing.kind)


class CastTests(unittest.TestCase):
    def test_resolved_cast_with_required_state_and_evidence_is_valid(self):
        spell = load_familiar()
        self.assertEqual([], validate_cast(spell, valid_cast(spell)))

    def test_missing_required_telemetry_blocks_ready_cast(self):
        spell = load_familiar()
        cast = valid_cast(spell)
        cast["status"] = "ready"
        cast["telemetry"] = [item for item in cast["telemetry"] if item["id"] != "holder_authority"]
        issues = validate_cast(spell, cast)
        self.assertTrue(any(issue.code == "telemetry-missing" for issue in issues))

    def test_blocked_cast_may_honestly_lack_required_telemetry(self):
        spell = load_familiar()
        cast = valid_cast(spell)
        cast["status"] = "blocked"
        cast.pop("actual_effect")
        cast["evidence"] = []
        cast["telemetry"] = []
        cast["requirements"] = []
        cast["limits"] = []
        self.assertEqual([], validate_cast(spell, cast))

    def test_exceeded_limit_invalidates_effectful_cast(self):
        spell = load_familiar()
        cast = valid_cast(spell)
        for limit in cast["limits"]:
            if limit["id"] == "holder-controls-form":
                limit["status"] = "exceeded"
        issues = validate_cast(spell, cast)
        self.assertTrue(any(issue.code == "limit-exceeded" for issue in issues))

    def test_resolved_cast_requires_effect_evidence(self):
        spell = load_familiar()
        cast = valid_cast(spell)
        cast["evidence"] = []
        issues = validate_cast(spell, cast)
        self.assertTrue(any(issue.code == "evidence-missing" for issue in issues))


if __name__ == "__main__":
    unittest.main()
