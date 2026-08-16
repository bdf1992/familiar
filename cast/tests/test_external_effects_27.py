"""Irreversible external effects and compensating Casts (issue #27).

Without an explicit model, a failed postcondition collapses three materially
different outcomes: no consequence, exact rollback, and persistent world
mutation requiring compensation. The third is not a worse version of the
second, and a runtime that cannot say which occurred cannot be trusted about
either.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest

from environment.authority import RecordingHostCredential, attenuated_credential_enforcer
from environment.consequence import (
    COMPENSATABLE,
    FAILED,
    NONE,
    REFUSED,
    RESIDUAL,
    REVERSED,
    SUCCEEDED,
    CompensationPath,
    ConsequenceError,
    ConsequenceFinding,
    compensate,
    verify_reversal,
)
from environment.scope import mapping_scope_enforcer
from kernel.spell_kernel import SpellKernel
from validation.candidate_adapter import load_candidate_spell
from validation.casting_04 import cast_with_binding

ROOT = Path(__file__).resolve().parents[1]
SPELL = ROOT / "validation" / "candidate" / "SPELL.md"
ADMISSIBLE_KEYS = ("id", "items", "done", "valid")


class RemoteLedger:
    """A stand-in external system. Sending cannot be un-sent; it can be voided."""

    def __init__(self):
        self.entries: list[str] = []
        self.voids: list[str] = []

    def post(self, entry: str) -> str:
        self.entries.append(entry)
        return entry

    def void(self, entry: str) -> str:
        if entry not in self.entries:
            raise RuntimeError(f"cannot void an entry that was never posted: {entry}")
        self.voids.append(entry)
        return entry


def target_observable(phase, context):
    from collections.abc import Mapping

    target = context.get("target")
    return isinstance(target, Mapping) and isinstance(target.get("items"), list)


def effect_confirmed(phase, context):
    return (context.get("target") or {}).get("done") is True


def binding(binding_id="external-technique"):
    return {
        "binding_format": "0.4-draft",
        "id": binding_id,
        "version": "1.0.0",
        "kind": "service",
        "realizes": {"spell": "bounded-work", "spell_version": "0.0.0", "effect": "act"},
        "mechanisms": {
            "authority": True,
            "scope": ["max_items"],
            "cost": ["tool_calls"],
            "duration": ["execution_max_ms"],
        },
    }


def make_kernel(executor, classifier=None, *, provider=None, executor_id=None):
    return SpellKernel(
        requirements={"target-observable": target_observable, "effect-confirmed": effect_confirmed},
        authority_resolver=lambda caster, permission, context: permission == "workspace.write",
        authority_enforcer=attenuated_credential_enforcer(RecordingHostCredential()),
        scope_resolver=lambda target, context: list(target["items"]),
        scope_enforcer=mapping_scope_enforcer(ADMISSIBLE_KEYS),
        consequence_classifier=classifier,
        compensation_provider=provider,
        executor_id=executor_id,
        executor=executor,
    )


def run(kernel, spell, **kwargs):
    return cast_with_binding(
        kernel, spell, binding(), effect_id="act",
        caster={"id": "agent-1", "kind": "agent"},
        target={"id": "one", "items": ["a"], "done": False},
        **kwargs,
    )


def consequence_observation(record):
    return next(
        item for item in record["observations"]
        if item["kind"] == "execution" and item["id"] == "consequence"
    )


class FindingShapeTests(unittest.TestCase):
    def test_a_compensatable_finding_must_name_its_path(self):
        with self.assertRaisesRegex(ConsequenceError, "must name its compensation path"):
            ConsequenceFinding(kind=COMPENSATABLE, observer="probe")

    def test_only_a_compensatable_finding_may_name_a_path(self):
        with self.assertRaisesRegex(ConsequenceError, "only compensatable may"):
            ConsequenceFinding(kind=RESIDUAL, observer="probe", compensation="void")

    def test_a_finding_requires_an_observer(self):
        with self.assertRaisesRegex(ConsequenceError, "requires an observer"):
            ConsequenceFinding(kind=NONE, observer="")

    def test_an_executor_cannot_certify_its_own_rollback(self):
        finding = ConsequenceFinding(kind=REVERSED, observer="the-technique")
        with self.assertRaisesRegex(ConsequenceError, "cannot certify its own rollback"):
            verify_reversal(finding, "the-technique")
        # An independent observer of the same reversal is fine.
        verify_reversal(ConsequenceFinding(kind=REVERSED, observer="fs-probe"), "the-technique")

    def test_only_persistent_kinds_report_persistent(self):
        self.assertFalse(ConsequenceFinding(kind=NONE, observer="p").persistent)
        self.assertFalse(ConsequenceFinding(kind=REVERSED, observer="p").persistent)
        self.assertTrue(ConsequenceFinding(kind=RESIDUAL, observer="p").persistent)
        self.assertTrue(
            ConsequenceFinding(kind=COMPENSATABLE, observer="p", compensation="void").persistent
        )


class IrreversibleEffectTests(unittest.TestCase):
    """The fixture the issue asks for: postcondition fails after a non-reversible effect."""

    def setUp(self):
        self.spell = load_candidate_spell(SPELL)

    def test_a_residual_survives_a_failed_postcondition(self):
        ledger = RemoteLedger()

        def post_then_fail(spell, effect_id, context, execution_max_ms):
            context["cost"]["charge"]("tool_calls")
            ledger.post("invoice-7")
            # The postcondition will fail: `done` is never set.
            return {"posted": "invoice-7"}

        def classifier(spell, effect_id, context, execution_failed):
            if ledger.entries and not ledger.voids:
                return ConsequenceFinding(
                    kind=RESIDUAL, observer="ledger-probe",
                    detail={"entries": list(ledger.entries)},
                )
            return ConsequenceFinding(kind=NONE, observer="ledger-probe")

        record = run(make_kernel(post_then_fail, classifier), self.spell)

        # The postcondition failed and the world kept the entry.
        self.assertEqual("partial", record["outcome"])
        self.assertEqual(["invoice-7"], ledger.entries)
        finding = consequence_observation(record)
        self.assertEqual("violated", finding["status"])
        self.assertEqual(RESIDUAL, finding["value"]["kind"])
        self.assertTrue(
            any("persistent world mutation (residual)" in item for item in record["residuals"])
        )

    def test_no_consequence_is_distinguished_from_a_residual(self):
        def touch_nothing(spell, effect_id, context, execution_max_ms):
            context["cost"]["charge"]("tool_calls")
            context["target"]["done"] = True
            return {}

        record = run(
            make_kernel(
                touch_nothing,
                lambda s, e, c, failed: ConsequenceFinding(kind=NONE, observer="ledger-probe"),
            ),
            self.spell,
        )

        self.assertEqual("resolved", record["outcome"])
        self.assertEqual("satisfied", consequence_observation(record)["status"])
        self.assertEqual([], record["residuals"])

    def test_an_exact_reversal_is_distinguished_from_a_residual(self):
        def act_and_undo(spell, effect_id, context, execution_max_ms):
            context["cost"]["charge"]("tool_calls")
            context["target"]["done"] = True
            return {}

        record = run(
            make_kernel(
                act_and_undo,
                lambda s, e, c, failed: ConsequenceFinding(
                    kind=REVERSED, observer="fs-probe", detail={"restored": ["a.txt"]},
                ),
                executor_id="the-technique",
            ),
            self.spell,
        )

        self.assertEqual("resolved", record["outcome"])
        self.assertEqual(REVERSED, consequence_observation(record)["value"]["kind"])
        self.assertEqual([], record["residuals"])

    def test_a_self_certified_reversal_is_refused_by_the_runtime(self):
        def act(spell, effect_id, context, execution_max_ms):
            context["cost"]["charge"]("tool_calls")
            context["target"]["done"] = True
            return {}

        record = run(
            make_kernel(
                act,
                lambda s, e, c, failed: ConsequenceFinding(kind=REVERSED, observer="the-technique"),
                executor_id="the-technique",
            ),
            self.spell,
        )

        observation = consequence_observation(record)
        self.assertEqual("unavailable", observation["status"])
        self.assertIn("cannot certify its own rollback", observation["detail"])
        self.assertTrue(any("consequence unclassified" in item for item in record["residuals"]))


class CompensationTests(unittest.TestCase):
    """The compensatable fixture: compensation does not erase original evidence."""

    def setUp(self):
        self.spell = load_candidate_spell(SPELL)

    def _compensatable_cast(self, ledger):
        def post_then_fail(spell, effect_id, context, execution_max_ms):
            context["cost"]["charge"]("tool_calls")
            ledger.post("invoice-9")
            return {"posted": "invoice-9"}

        def classifier(spell, effect_id, context, execution_failed):
            return ConsequenceFinding(
                kind=COMPENSATABLE, observer="ledger-probe",
                detail={"entries": list(ledger.entries)}, compensation="ledger.void",
            )

        path = CompensationPath(
            id="ledger.void", provider="remote-ledger",
            compensate=lambda context: ledger.void(context["entry"]),
        )
        record = run(make_kernel(post_then_fail, classifier, provider=path), self.spell)
        finding = ConsequenceFinding(
            kind=COMPENSATABLE, observer="ledger-probe",
            detail={"entries": list(ledger.entries)}, compensation="ledger.void",
        )
        return record, finding, path

    def test_successful_compensation_does_not_erase_the_original_evidence(self):
        ledger = RemoteLedger()
        record, finding, path = self._compensatable_cast(ledger)
        before = deepcopy(record)

        compensation = compensate(record, finding, path, {"entry": "invoice-9"})

        self.assertEqual(SUCCEEDED, compensation.status)
        self.assertEqual(["invoice-9"], ledger.voids)
        # The original record is untouched, residual and all.
        self.assertEqual(before, record)
        self.assertTrue(
            any("persistent world mutation (compensatable)" in item for item in record["residuals"])
        )
        # The compensation is a separate attributable event linked to the Cast.
        self.assertEqual(record["cast_id"], compensation.original_cast_id)
        self.assertEqual(COMPENSATABLE, compensation.original_finding["kind"])

    def test_compensation_failure_remains_visible_and_rewrites_nothing(self):
        ledger = RemoteLedger()
        record, finding, path = self._compensatable_cast(ledger)
        before = deepcopy(record)

        # Void an entry that was never posted: the provider refuses.
        compensation = compensate(record, finding, path, {"entry": "invoice-does-not-exist"})

        self.assertEqual(FAILED, compensation.status)
        self.assertIn("never posted", compensation.detail["error"])
        self.assertEqual([], ledger.voids)
        self.assertEqual(before, record)
        self.assertEqual(COMPENSATABLE, compensation.original_finding["kind"])

    def test_compensation_is_refused_for_a_consequence_that_is_not_compensatable(self):
        ledger = RemoteLedger()
        record, _finding, path = self._compensatable_cast(ledger)
        residual = ConsequenceFinding(kind=RESIDUAL, observer="ledger-probe")

        compensation = compensate(record, residual, path, {"entry": "invoice-9"})

        self.assertEqual(REFUSED, compensation.status)
        self.assertIn("not compensatable", compensation.detail["reason"])
        self.assertEqual([], ledger.voids)

    def test_compensation_is_refused_when_the_finding_names_another_path(self):
        ledger = RemoteLedger()
        record, _finding, path = self._compensatable_cast(ledger)
        elsewhere = ConsequenceFinding(
            kind=COMPENSATABLE, observer="ledger-probe", compensation="some.other.path",
        )

        compensation = compensate(record, elsewhere, path, {"entry": "invoice-9"})

        self.assertEqual(REFUSED, compensation.status)
        self.assertIn("some.other.path", compensation.detail["reason"])
        self.assertEqual([], ledger.voids)


class ClosureRefusalTests(unittest.TestCase):
    def setUp(self):
        self.spell = load_candidate_spell(SPELL)

    def test_closure_refuses_when_compensation_is_required_and_none_exists(self):
        calls = []

        def never(spell, effect_id, context, execution_max_ms):
            calls.append("executed")
            return {}

        record = run(make_kernel(never), self.spell, compensation_required=True)

        self.assertEqual([], calls)
        self.assertEqual("refused", record["closure"]["decision"])
        self.assertTrue(
            any("compensation-unsupported" in reason for reason in record["closure"]["reasons"])
        )
        self.assertIsNone(record["outcome"])

    def test_closure_proceeds_when_a_compensation_provider_is_registered(self):
        def act(spell, effect_id, context, execution_max_ms):
            context["cost"]["charge"]("tool_calls")
            context["target"]["done"] = True
            return {}

        path = CompensationPath(id="ledger.void", provider="remote-ledger",
                                compensate=lambda context: None)
        record = run(make_kernel(act, provider=path), self.spell, compensation_required=True)

        self.assertEqual("closed", record["closure"]["decision"])
        self.assertEqual("resolved", record["outcome"])

    def test_not_every_effect_must_be_reversible(self):
        """Compensation is opt-in. An ordinary Cast declares nothing and still closes."""
        def act(spell, effect_id, context, execution_max_ms):
            context["cost"]["charge"]("tool_calls")
            context["target"]["done"] = True
            return {}

        record = run(make_kernel(act), self.spell)
        self.assertEqual("resolved", record["outcome"])
        self.assertEqual(
            [],
            [item for item in record["observations"] if item["id"] == "consequence"],
        )


if __name__ == "__main__":
    unittest.main()
