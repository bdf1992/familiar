"""Maintenance replay is guarded on three independent identities (issue #12).

`environment/MAGIC.md` defines one Maintenance Act and one consequence
boundary. The runtime recorded only `act_id = source_kind:domain:source_id`,
which left two ways to buy a second consequence with one execution: rebind the
same source to another domain, or reuse one accepted verifier receipt under a
fresh act id. A verifier response is not reusable authority.
"""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from environment.magic import (
    ConsequenceDecision,
    MagicLimits,
    MagicRuntime,
    MagicRuntimeError,
    MaintenanceDecision,
    MaintenanceEvidence,
)


def limits(**overrides):
    value = dict(
        max_network=6,
        max_local=5,
        max_personal=3,
        max_cast=2,
        max_committed=4,
        max_restored=1,
        max_level=3,
        drain_rate=1,
    )
    value.update(overrides)
    return MagicLimits(**value)


def evidence(*, source_id="maintain-1", domain="environment", source_kind="skill", mechanism="mana-drain"):
    return MaintenanceEvidence(
        source_kind=source_kind,
        source_id=source_id,
        domain=domain,
        mechanism=mechanism,
        before={"healthy": False},
        after={"healthy": True},
    )


def runtime(*, path=None, receipt=None, restorable=2, spent=1):
    """A runtime whose maintenance receipts can be forced to collide.

    ``receipt=None`` keeps the per-act receipt the rest of the suite uses.
    A fixed string makes one accepted receipt reappear under a fresh act id,
    which is the second replay route this issue closes.
    """

    def maintenance_verifier(proof):
        return MaintenanceDecision(
            confirmed=bool(proof.after.get("healthy")),
            restorable=restorable,
            observer="independent-probe",
            receipt_id=receipt if receipt is not None else f"maintenance:{proof.act_id}",
            reason="mechanism restored",
        )

    return MagicRuntime(
        10,
        limits(),
        path=path,
        access_resolver=lambda actor, operation, locality: actor in {"bdo", "owl"} and locality in {"network", "lab"},
        route_resolver=lambda source, target: (source, target) in {("network", "lab"), ("lab", "network")},
        role_resolver=lambda actor, role, domain: actor == "owl" and role == "domains-maintainer",
        maintenance_verifier=maintenance_verifier,
        consequence_verifier=lambda cast_id, commitment: ConsequenceDecision(
            confirmed=True,
            spent=min(spent, commitment["amount"]),
            observer="independent-probe",
            receipt_id=f"consequence:{cast_id}",
            reason="observed consequence",
        ),
    )


def spend_one(magic, cast_id="cast-1"):
    """Put one Mana into Spent so restoration has something eligible."""
    magic.claim("bdo", "network", 1)
    magic.commit(cast_id, "bdo", "network", 1)
    magic.settle(cast_id)


class SourceIdentityReplayTests(unittest.TestCase):
    def test_the_same_source_cannot_become_a_second_act_under_another_domain(self):
        magic = runtime()
        spend_one(magic)
        magic.restore("owl", "network", evidence(source_id="probe-1", domain="environment"))
        for domain in ("cast", "familiar", "registry", "spell"):
            with self.subTest(rebound_to=domain):
                with self.assertRaisesRegex(MagicRuntimeError, "source already consumed"):
                    magic.restore("owl", "network", evidence(source_id="probe-1", domain=domain))

    def test_the_same_source_cannot_become_a_second_act_under_another_mechanism(self):
        """Mechanism is not part of act_id, so the act guard is what refuses here.

        The issue requires refusal regardless of claimed domain or mechanism;
        it does not require one named guard to be the one that fires.
        """
        magic = runtime()
        spend_one(magic)
        magic.restore("owl", "network", evidence(source_id="probe-1", mechanism="mana-drain"))
        with self.assertRaisesRegex(MagicRuntimeError, "already applied|already consumed"):
            magic.restore("owl", "network", evidence(source_id="probe-1", mechanism="some-other-mechanism"))

    def test_source_kind_still_separates_two_genuinely_different_sources(self):
        magic = runtime()
        spend_one(magic)
        magic.restore("owl", "network", evidence(source_id="probe-1", source_kind="skill"))
        # A cast with the same id string is a different attributable source.
        magic.restore("owl", "network", evidence(source_id="probe-1", source_kind="cast"))
        self.assertEqual(10, magic.total())

    def test_the_exact_act_remains_one_use(self):
        magic = runtime()
        spend_one(magic)
        proof = evidence(source_id="probe-1")
        magic.restore("owl", "network", proof)
        with self.assertRaisesRegex(MagicRuntimeError, "already applied|already consumed"):
            magic.restore("owl", "network", proof)


class ReceiptReplayTests(unittest.TestCase):
    def test_one_accepted_receipt_closes_at_most_one_consequence(self):
        magic = runtime(receipt="receipt-reused")
        spend_one(magic)
        magic.restore("owl", "network", evidence(source_id="probe-1"))
        with self.assertRaisesRegex(MagicRuntimeError, "receipt already consumed"):
            magic.restore("owl", "network", evidence(source_id="probe-2"))

    def test_a_receipt_accepted_for_restoration_cannot_also_configure(self):
        magic = runtime(receipt="receipt-reused")
        spend_one(magic)
        magic.restore("owl", "network", evidence(source_id="probe-1"))
        with self.assertRaisesRegex(MagicRuntimeError, "receipt already consumed"):
            magic.configure(
                "owl",
                {"max_personal": 2},
                evidence(source_id="probe-2", mechanism=MagicRuntime.SETTINGS_MECHANISM),
            )


class SharedBoundaryTests(unittest.TestCase):
    """Restoration and runtime configuration share one replay boundary."""

    def test_a_source_consumed_by_restoration_cannot_configure(self):
        """Restoration under one domain, configuration under another, one source.

        `configure` requires domain `environment`, so restoring under `cast`
        first makes the two act ids genuinely different. Only source identity
        can refuse this, which is the point.
        """
        magic = runtime()
        spend_one(magic)
        magic.restore("owl", "network", evidence(source_id="shared-source", domain="cast"))
        with self.assertRaisesRegex(MagicRuntimeError, "source already consumed"):
            magic.configure(
                "owl",
                {"max_personal": 2},
                evidence(source_id="shared-source", mechanism=MagicRuntime.SETTINGS_MECHANISM),
            )

    def test_a_source_consumed_by_configuration_cannot_restore(self):
        magic = runtime()
        spend_one(magic)
        magic.configure(
            "owl",
            {"max_personal": 2},
            evidence(source_id="shared-source", mechanism=MagicRuntime.SETTINGS_MECHANISM),
        )
        with self.assertRaisesRegex(MagicRuntimeError, "source already consumed"):
            magic.restore("owl", "network", evidence(source_id="shared-source", domain="cast"))


class RestartReplayTests(unittest.TestCase):
    def test_all_three_guards_survive_a_persisted_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "magic.json"
            writer = runtime(path=path, receipt="receipt-reused")
            spend_one(writer)
            writer.restore("owl", "network", evidence(source_id="probe-1", domain="environment"))

            reopened = runtime(path=path, receipt="receipt-reused")

            with self.assertRaisesRegex(MagicRuntimeError, "already applied|already consumed"):
                reopened.restore("owl", "network", evidence(source_id="probe-1", domain="environment"))
            with self.assertRaisesRegex(MagicRuntimeError, "source already consumed"):
                reopened.restore("owl", "network", evidence(source_id="probe-1", domain="cast"))
            with self.assertRaisesRegex(MagicRuntimeError, "receipt already consumed"):
                reopened.restore("owl", "network", evidence(source_id="probe-2"))

            self.assertEqual(10, reopened.total())

    def test_a_ledger_holding_a_duplicated_maintenance_event_is_refused_on_open(self):
        """The guard lives in the applier, so replay cannot reconstruct past it."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "magic.json"
            writer = runtime(path=path, restorable=0)
            writer.restore("owl", "network", evidence(source_id="probe-1"))

            payload = json.loads(path.read_text(encoding="utf-8"))
            events = payload["events"]
            original = next(event for event in events if event["operation"] == "maintenance")

            duplicate = dict(original)
            duplicate["sequence"] = len(events)
            duplicate["previous_digest"] = events[-1]["digest"]
            material = {
                "sequence": duplicate["sequence"],
                "operation": duplicate["operation"],
                "actor": duplicate["actor"],
                "locality": duplicate["locality"],
                "amount": duplicate["amount"],
                "details": duplicate["details"],
                "previous_digest": duplicate["previous_digest"],
            }
            duplicate["digest"] = MagicRuntime._event_digest(material)
            events.append(duplicate)
            path.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")), encoding="utf-8")

            with self.assertRaisesRegex(MagicRuntimeError, "already applied|already consumed"):
                runtime(path=path, restorable=0)


class ConservationTests(unittest.TestCase):
    def test_a_refused_replay_moves_no_mana(self):
        magic = runtime(receipt="receipt-reused")
        spend_one(magic)
        magic.restore("owl", "network", evidence(source_id="probe-1"))
        before = (magic.total(), magic.spent_total(), dict(magic.sense("owl", "network")))

        for attempt in (
            evidence(source_id="probe-1", domain="cast"),
            evidence(source_id="probe-2"),
        ):
            with self.assertRaises(MagicRuntimeError):
                magic.restore("owl", "network", attempt)

        self.assertEqual(before, (magic.total(), magic.spent_total(), dict(magic.sense("owl", "network"))))
        self.assertEqual(10, magic.total())


if __name__ == "__main__":
    unittest.main()
