"""Immutable CAST 0.7 sealing specimens for issue #36."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import unittest

import jsonschema

from cast.practitioner.cast_record import (
    CAST_RECORD_VERSION,
    CastSealingError,
    canonical_record_material,
    record_digest,
    seal_cast,
    seal_crossing,
    seal_refusal,
)
from cast.practitioner.observation import ExecutorClaim, evaluate_crossing_observations
from environment.magic import ManaEvent
from test_observation_35 import closed_attempt, consequence, observation


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "cast" / "kernel" / "0.7-draft" / "cast.schema.json"
SPEC = ROOT / "cast" / "kernel" / "0.7-draft" / "CAST.md"


def schema() -> dict:
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def observed_account(*, value: str = "ready", executor_success: bool = True):
    _view, _attached, closed, cast_id = closed_attempt()
    account = evaluate_crossing_observations(
        closed,
        cast_id,
        executor_claim=ExecutorClaim(executor_success, result="executor-result"),
        observations=(observation(cast_id, "obs:seal", value),),
        consequence=consequence(mana_spent=1),
        mana_participant="bdo",
    )
    return closed, cast_id, account


def mana_events(cast_id: str) -> tuple[ManaEvent, ManaEvent]:
    commit = ManaEvent(
        sequence=10,
        operation="commit",
        actor="bdo",
        locality="network",
        amount=2,
        details={"cast_id": cast_id, "level": None},
        previous_digest="sha256:" + "1" * 64,
        digest="sha256:" + "2" * 64,
    )
    settle = ManaEvent(
        sequence=11,
        operation="settle",
        actor="bdo",
        locality="network",
        amount=2,
        details={
            "cast_id": cast_id,
            "spent": 1,
            "released": 1,
            "decision": {
                "confirmed": True,
                "spent": 1,
                "observer": "observer:consequence",
                "receipt_id": "observation-account:example",
                "reason": "independent evidence",
            },
        },
        previous_digest=commit.digest,
        digest="sha256:" + "3" * 64,
    )
    return commit, settle


def generic_material(status: str = "successful") -> dict:
    return {
        "cast_format": CAST_RECORD_VERSION,
        "cast_id": "cast:generic",
        "plan_digest": None if status == "refused" else "sha256:" + "a" * 64,
        "recorded_configuration": {"target": "x", "caster": "y"},
        "capability_match_evidence": {},
        "enforced_handle_receipts": {},
        "mana_transitions": [],
        "obligation_findings": [],
        "observations": [],
        "execution_trace": {"attempted": status != "refused", "events": []},
        "outcome": {},
        "residuals": [],
        "mana_settlement": None,
        "status": status,
    }


class CanonicalIdentityTests(unittest.TestCase):
    def test_canonically_equivalent_mapping_order_has_same_record_digest(self):
        first = generic_material()
        second = {key: deepcopy(first[key]) for key in reversed(tuple(first))}
        second["recorded_configuration"] = {"caster": "y", "target": "x"}

        self.assertEqual(record_digest(first), record_digest(second))
        self.assertEqual(seal_cast(first).record_digest, seal_cast(second).record_digest)

    def test_material_change_changes_record_digest(self):
        first = generic_material()
        second = deepcopy(first)
        second["outcome"] = {"consequence": "different"}
        self.assertNotEqual(record_digest(first), record_digest(second))

    def test_record_digest_field_cannot_choose_its_own_identity(self):
        first = generic_material()
        forged = deepcopy(first)
        forged["record_digest"] = "sha256:" + "f" * 64
        self.assertEqual(record_digest(first), record_digest(forged))

    def test_caller_mutation_after_sealing_cannot_rewrite_record(self):
        source = generic_material()
        sealed = seal_cast(source)
        before = sealed.material()

        source["recorded_configuration"]["target"] = "mutated caller"
        source["outcome"]["late"] = True

        self.assertEqual(before, sealed.material())
        self.assertEqual(before["record_digest"], sealed.record_digest)

    def test_mutating_a_readback_cannot_rewrite_record(self):
        sealed = seal_cast(generic_material())
        readback = sealed.material()
        readback["recorded_configuration"]["target"] = "mutated reader"
        self.assertEqual("x", sealed.material()["recorded_configuration"]["target"])


class SchemaAndStatusTests(unittest.TestCase):
    def test_every_supported_status_is_schema_valid(self):
        for status in ("successful", "refused", "aborted", "violated", "unresolved"):
            with self.subTest(status=status):
                record = seal_cast(generic_material(status)).material()
                jsonschema.validate(record, schema())

    def test_preclosure_refusal_has_no_fake_plan_digest(self):
        record = seal_refusal(
            "cast:refused",
            recorded_configuration={"target": "missing"},
            refusal_reasons=("capability gap",),
            observations=({"observer": "environment", "status": "unavailable"},),
        ).material()
        self.assertEqual("refused", record["status"])
        self.assertIsNone(record["plan_digest"])
        self.assertFalse(record["execution_trace"]["attempted"])
        jsonschema.validate(record, schema())

    def test_non_refusal_cannot_seal_without_closed_plan_identity(self):
        material = generic_material("successful")
        material["plan_digest"] = None
        with self.assertRaisesRegex(CastSealingError, "requires plan_digest"):
            seal_cast(material)

    def test_refusal_cannot_claim_a_plan_that_never_closed(self):
        material = generic_material("refused")
        material["plan_digest"] = "sha256:" + "a" * 64
        with self.assertRaisesRegex(CastSealingError, "must not claim"):
            seal_cast(material)

    def test_docs_keep_integrity_trust_and_effect_standing_distinct(self):
        text = SPEC.read_text(encoding="utf-8")
        for law in (
            "record_digest != truth",
            "record_digest != signature",
            "signature != correctness",
            "finding provenance != authority",
            "executor success != Effect realization",
        ):
            self.assertIn(law, text)


class CrossingCompositionTests(unittest.TestCase):
    def test_real_closed_plan_and_observation_account_seal_together(self):
        closed, cast_id, account = observed_account()
        events = mana_events(cast_id)
        sealed = seal_crossing(
            closed,
            account,
            mana_events=events,
            residuals=({"kind": "observed-residual", "present": True},),
            execution_trace=({"step": "technique returned"},),
        )
        record = sealed.material()

        self.assertEqual(cast_id, record["cast_id"])
        self.assertEqual(closed.digest, record["plan_digest"])
        self.assertTrue(record["capability_match_evidence"])
        self.assertTrue(record["enforced_handle_receipts"])
        self.assertEqual(["commit", "settle"], [item["operation"] for item in record["mana_transitions"]])
        self.assertEqual("discharged", next(item for item in record["obligation_findings"] if item["obligation_id"] == "post-state")["status"])
        self.assertEqual("obs:seal", record["observations"][0]["id"])
        self.assertTrue(record["execution_trace"]["executor_claim"]["succeeded"])
        self.assertEqual("residual", record["outcome"]["consequence"]["kind"])
        self.assertEqual("settle", record["mana_settlement"]["operation"])
        self.assertEqual("successful", record["status"])
        jsonschema.validate(record, schema())

    def test_executor_success_does_not_make_a_violated_crossing_successful(self):
        closed, cast_id, account = observed_account(value="broken", executor_success=True)
        record = seal_crossing(closed, account, mana_events=mana_events(cast_id)).material()
        self.assertTrue(record["execution_trace"]["executor_claim"]["succeeded"])
        self.assertEqual("violated", record["status"])

    def test_executor_failure_can_seal_as_aborted_without_erasing_consequence(self):
        closed, cast_id, account = observed_account(value="ready", executor_success=False)
        record = seal_crossing(closed, account, mana_events=mana_events(cast_id)).material()
        self.assertEqual("aborted", record["status"])
        self.assertEqual("residual", record["outcome"]["consequence"]["kind"])

    def test_unknown_evidence_seals_as_unresolved_not_success(self):
        _view, _attached, closed, cast_id = closed_attempt()
        account = evaluate_crossing_observations(
            closed,
            cast_id,
            executor_claim=ExecutorClaim(True),
            observations=(observation(cast_id, "obs:unknown", status="unknown"),),
            consequence=consequence(mana_spent=1),
            mana_participant="bdo",
        )
        record = seal_crossing(closed, account, mana_events=mana_events(cast_id)).material()
        self.assertEqual("unresolved", record["status"])
        self.assertIn("post-state", record["outcome"]["unknown"])

    def test_account_for_another_plan_refuses(self):
        closed, cast_id, account = observed_account()
        forged = replace(account, plan_digest="sha256:" + "0" * 64)
        with self.assertRaisesRegex(CastSealingError, "another ClosedPlan"):
            seal_crossing(closed, forged, mana_events=mana_events(cast_id))

    def test_mana_event_for_another_cast_refuses(self):
        closed, _cast_id, account = observed_account()
        bad = ManaEvent(
            sequence=1,
            operation="commit",
            actor="bdo",
            locality="network",
            amount=1,
            details={"cast_id": "another-cast"},
            previous_digest=None,
            digest="sha256:" + "9" * 64,
        )
        with self.assertRaisesRegex(CastSealingError, "another Cast"):
            seal_crossing(closed, account, mana_events=(bad,))

    def test_record_material_exposes_exact_plan_configuration_not_hash_only(self):
        closed, cast_id, account = observed_account()
        record = seal_crossing(closed, account, mana_events=mana_events(cast_id)).material()
        canonical = canonical_record_material(record)
        self.assertEqual(closed.plan.configuration, canonical["recorded_configuration"])
        self.assertNotIn("record_digest", canonical)


if __name__ == "__main__":
    unittest.main()
