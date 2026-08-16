from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from environment.magic import MagicLimits, MagicRuntime, MagicRuntimeError, MaintenanceEvidence


def limits(**overrides):
    value = dict(
        total_mana=10,
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


def evidence(*, domain="environment", source_kind="skill", mechanism="mana-drain"):
    return MaintenanceEvidence(
        source_kind=source_kind,
        source_id="maintain-1",
        domain=domain,
        mechanism=mechanism,
        before={"healthy": False},
        after={"healthy": True},
        observer="independent-probe",
    )


class MagicRuntime06Tests(unittest.TestCase):
    def runtime(self, **kwargs):
        return MagicRuntime(
            limits(),
            role_resolver=lambda actor, role, domain: actor == "owl" and role == "domains-maintainer",
            maintenance_verifier=lambda proof: 2 if proof.after.get("healthy") else 0,
            **kwargs,
        )

    def test_conservation_through_claim_commit_partial_settle_and_release(self):
        runtime = self.runtime()
        runtime.claim("bdo", "network", 3)
        runtime.commit("cast-1", "bdo", "network", 2, level=1)
        runtime.settle("cast-1", spent=1)
        runtime.release("bdo", "network", 2)
        self.assertEqual(10, runtime.total())
        self.assertEqual({"ambient": 9, "claimed": 0, "subject_claimed": 0}, runtime.sense("network", subject="bdo"))

    def test_shared_sense_and_personal_claim_limit(self):
        runtime = self.runtime()
        runtime.claim("bdo", "network", 2)
        runtime.claim("owl", "network", 1)
        self.assertEqual({"ambient": 7, "claimed": 3, "subject_claimed": 2}, runtime.sense("network", subject="bdo"))
        with self.assertRaisesRegex(MagicRuntimeError, "max_personal"):
            runtime.claim("bdo", "network", 2)

    def test_network_and_local_limits_prevent_double_claim_pressure(self):
        runtime = self.runtime()
        runtime.claim("a", "network", 3)
        runtime.claim("b", "network", 2)
        with self.assertRaisesRegex(MagicRuntimeError, "max_local"):
            runtime.claim("c", "network", 1)
        self.assertEqual(10, runtime.total())

    def test_drain_returns_claimed_mana_to_same_ambient_locality(self):
        runtime = self.runtime()
        runtime.claim("bdo", "network", 3)
        runtime.drain(ticks=2)
        self.assertEqual({"ambient": 9, "claimed": 1, "subject_claimed": 1}, runtime.sense("network", subject="bdo"))
        self.assertEqual("drain", runtime.events[-1].operation)
        self.assertEqual(10, runtime.total())

    def test_commit_requires_claim_and_level_admission(self):
        runtime = self.runtime()
        runtime.claim("bdo", "network", 2)
        with self.assertRaisesRegex(MagicRuntimeError, "max_level"):
            runtime.commit("cast-high", "bdo", "network", 1, level=4)
        runtime.commit("cast-ok", "bdo", "network", 2, level=3)
        with self.assertRaisesRegex(MagicRuntimeError, "insufficient claimed"):
            runtime.commit("cast-no-mana", "bdo", "network", 1)

    def test_maintenance_restores_spent_mana_only_to_ambient_and_applies_ceiling(self):
        runtime = self.runtime()
        runtime.claim("bdo", "network", 2)
        runtime.commit("cast-1", "bdo", "network", 2)
        runtime.settle("cast-1", spent=2)
        event = runtime.restore("owl", "network", evidence())
        self.assertEqual(1, event.amount)
        self.assertEqual(0, runtime.claimed_by("owl"))
        self.assertEqual({"ambient": 9, "claimed": 0}, runtime.sense("network"))
        self.assertEqual(10, runtime.total())

    def test_maintenance_requires_role_and_independent_verifier(self):
        runtime = self.runtime()
        runtime.claim("bdo", "network", 1)
        runtime.commit("cast-1", "bdo", "network", 1)
        runtime.settle("cast-1", spent=1)
        with self.assertRaisesRegex(MagicRuntimeError, "Domains Maintainer"):
            runtime.restore("bdo", "network", evidence())
        no_verifier = MagicRuntime(limits(), role_resolver=lambda *_: True)
        no_verifier.claim("bdo", "network", 1)
        no_verifier.commit("cast-1", "bdo", "network", 1)
        no_verifier.settle("cast-1", spent=1)
        with self.assertRaisesRegex(MagicRuntimeError, "verifier unavailable"):
            no_verifier.restore("owl", "network", evidence())

    def test_skill_and_cast_evidence_use_same_restoration_path(self):
        for source_kind in ("skill", "cast"):
            runtime = self.runtime()
            runtime.claim("bdo", "network", 1)
            runtime.commit("cast-1", "bdo", "network", 1)
            runtime.settle("cast-1", spent=1)
            event = runtime.restore("owl", "network", evidence(source_kind=source_kind))
            self.assertEqual(source_kind, event.details["evidence"]["source_kind"])
            self.assertEqual(10, runtime.total())

    def test_domains_maintainer_can_change_runtime_setting_but_not_total_mana(self):
        runtime = self.runtime()
        event = runtime.configure("owl", {"max_personal": 4, "max_cast": 3}, evidence())
        self.assertEqual(4, runtime.limits.max_personal)
        self.assertEqual("configure", event.operation)
        with self.assertRaisesRegex(MagicRuntimeError, "total_mana is conserved"):
            runtime.configure("owl", {"total_mana": 11}, evidence())

    def test_runtime_refuses_setting_change_that_invalidates_live_claim(self):
        runtime = self.runtime()
        runtime.claim("bdo", "network", 3)
        with self.assertRaisesRegex(MagicRuntimeError, "max_personal"):
            runtime.configure("owl", {"max_personal": 2, "max_cast": 2}, evidence())

    def test_restart_replays_exact_conserved_state(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "magic.json"
            runtime = self.runtime(path=path)
            runtime.claim("bdo", "network", 2)
            runtime.commit("cast-1", "bdo", "network", 1)
            runtime.settle("cast-1", spent=1)
            reopened = self.runtime(path=path)
            self.assertEqual(10, reopened.total())
            self.assertEqual(runtime.sense("network", subject="bdo"), reopened.sense("network", subject="bdo"))
            self.assertEqual(len(runtime.events), len(reopened.events))

    def test_tampered_ledger_refuses_open(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "magic.json"
            runtime = self.runtime(path=path)
            runtime.claim("bdo", "network", 1)
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["events"][-1]["amount"] = 2
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(MagicRuntimeError, "digest mismatch"):
                self.runtime(path=path)


if __name__ == "__main__":
    unittest.main()
