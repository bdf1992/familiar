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


class MagicRuntime06Tests(unittest.TestCase):
    def runtime(self, **kwargs):
        allowed = kwargs.pop("allowed", {"bdo", "owl", "a", "b", "c"})
        spent = kwargs.pop("spent", 1)
        observer = kwargs.pop("observer", "independent-probe")
        maintenance_observer = kwargs.pop("maintenance_observer", observer)
        consequence_observer = kwargs.pop("consequence_observer", observer)
        return MagicRuntime(
            10,
            limits(),
            access_resolver=lambda actor, operation, locality: actor in allowed and locality in {"network", "lab"},
            route_resolver=lambda source, target: (source, target) in {("network", "lab"), ("lab", "network")},
            role_resolver=lambda actor, role, domain: actor == "owl" and role == "domains-maintainer",
            maintenance_verifier=lambda proof: MaintenanceDecision(
                confirmed=bool(proof.after.get("healthy")),
                restorable=2,
                observer=maintenance_observer,
                receipt_id=f"maintenance:{proof.act_id}",
                reason="mechanism restored",
            ),
            consequence_verifier=lambda cast_id, commitment: ConsequenceDecision(
                confirmed=True,
                spent=min(spent, commitment["amount"]),
                observer=consequence_observer,
                receipt_id=f"consequence:{cast_id}",
                reason="observed consequence",
            ),
            **kwargs,
        )

    def test_conservation_through_claim_commit_partial_settle_and_release(self):
        runtime = self.runtime(spent=1)
        runtime.claim("bdo", "network", 3)
        runtime.commit("cast-1", "bdo", "network", 2, level=1)
        runtime.settle("cast-1")
        runtime.release("bdo", "network", 2)
        self.assertEqual(10, runtime.total())
        self.assertEqual({"ambient": 9, "claimed": 0, "subject_claimed": 0}, runtime.sense("bdo", "network", subject="bdo"))
        self.assertEqual(1, runtime.spent_total(locality="network"))

    def test_magic_participation_and_reach_are_required_for_sense_and_claim(self):
        runtime = self.runtime()
        with self.assertRaisesRegex(MagicRuntimeError, "magic access unavailable"):
            runtime.sense("stranger", "network")
        with self.assertRaisesRegex(MagicRuntimeError, "magic access unavailable"):
            runtime.claim("stranger", "network", 1)
        with self.assertRaisesRegex(MagicRuntimeError, "magic access unavailable"):
            runtime.claim("bdo", "elsewhere", 1)

    def test_ambient_mana_flows_only_over_environment_route(self):
        runtime = self.runtime()
        runtime.flow("network", "lab", 4)
        self.assertEqual({"ambient": 4, "claimed": 0}, runtime.sense("bdo", "lab"))
        self.assertEqual({"ambient": 6, "claimed": 0}, runtime.sense("bdo", "network"))
        self.assertEqual(10, runtime.total())
        with self.assertRaisesRegex(MagicRuntimeError, "route unavailable"):
            runtime.flow("network", "moon", 1)

    def test_shared_sense_and_personal_claim_limit(self):
        runtime = self.runtime()
        runtime.claim("bdo", "network", 2)
        runtime.claim("owl", "network", 1)
        self.assertEqual({"ambient": 7, "claimed": 3, "subject_claimed": 2}, runtime.sense("owl", "network", subject="bdo"))
        with self.assertRaisesRegex(MagicRuntimeError, "max_personal"):
            runtime.claim("bdo", "network", 2)

    def test_network_and_local_limits_bound_active_mana_not_ambient_mana(self):
        runtime = self.runtime()
        runtime.claim("a", "network", 3)
        runtime.claim("b", "network", 2)
        with self.assertRaisesRegex(MagicRuntimeError, "max_local"):
            runtime.claim("c", "network", 1)
        runtime.flow("network", "lab", 3)
        self.assertEqual(10, runtime.total())
        self.assertEqual(3, runtime.sense("a", "lab")["ambient"])

    def test_drain_returns_claimed_mana_to_same_ambient_locality(self):
        runtime = self.runtime()
        runtime.claim("bdo", "network", 3)
        runtime.drain(ticks=2)
        self.assertEqual({"ambient": 9, "claimed": 1, "subject_claimed": 1}, runtime.sense("bdo", "network", subject="bdo"))
        self.assertEqual("drain", runtime.events[-1].operation)
        self.assertEqual(10, runtime.total())

    def test_commit_requires_claim_access_and_level_admission(self):
        runtime = self.runtime()
        runtime.claim("bdo", "network", 2)
        with self.assertRaisesRegex(MagicRuntimeError, "max_level"):
            runtime.commit("cast-high", "bdo", "network", 1, level=4)
        runtime.commit("cast-ok", "bdo", "network", 2, level=3)
        with self.assertRaisesRegex(MagicRuntimeError, "insufficient claimed"):
            runtime.commit("cast-no-mana", "bdo", "network", 1)

    def test_settlement_requires_environment_consequence_verifier(self):
        runtime = MagicRuntime(10, limits(), access_resolver=lambda *_: True)
        runtime.claim("bdo", "network", 1)
        runtime.commit("cast-1", "bdo", "network", 1)
        with self.assertRaisesRegex(MagicRuntimeError, "consequence verifier unavailable"):
            runtime.settle("cast-1")
        self.assertEqual(1, runtime.committed_by("bdo"))

    def test_settlement_refuses_self_observed_consequence(self):
        runtime = self.runtime(consequence_observer="bdo")
        runtime.claim("bdo", "network", 1)
        runtime.commit("cast-1", "bdo", "network", 1)
        with self.assertRaisesRegex(MagicRuntimeError, "independent consequence observer"):
            runtime.settle("cast-1")

    def test_cast_id_cannot_be_reused_after_settlement(self):
        runtime = self.runtime(spent=0)
        runtime.claim("bdo", "network", 2)
        runtime.commit("cast-1", "bdo", "network", 1)
        runtime.settle("cast-1")
        with self.assertRaisesRegex(MagicRuntimeError, "cast id already used"):
            runtime.commit("cast-1", "bdo", "network", 1)

    def test_spent_mana_retains_cast_provenance_through_restoration(self):
        runtime = self.runtime(spent=1)
        runtime.claim("bdo", "network", 2)
        runtime.commit("cast-1", "bdo", "network", 1)
        runtime.settle("cast-1")
        runtime.commit("cast-2", "bdo", "network", 1)
        runtime.settle("cast-2")
        event = runtime.restore("owl", "network", evidence())
        self.assertEqual([{"cast_id": "cast-1", "amount": 1}], event.details["restored_from"])
        self.assertEqual(1, runtime.spent_total(locality="network"))
        self.assertEqual(10, runtime.total())

    def test_maintenance_restores_spent_only_to_ambient_and_applies_ceiling(self):
        runtime = self.runtime(spent=2)
        runtime.claim("bdo", "network", 2)
        runtime.commit("cast-1", "bdo", "network", 2)
        runtime.settle("cast-1")
        event = runtime.restore("owl", "network", evidence())
        self.assertEqual("maintenance", event.operation)
        self.assertEqual(1, event.amount)
        self.assertEqual(0, runtime.claimed_by("owl"))
        self.assertEqual({"ambient": 9, "claimed": 0}, runtime.sense("owl", "network"))
        self.assertEqual(10, runtime.total())

    def test_confirmed_zero_restoration_still_consumes_maintenance_act(self):
        runtime = self.runtime()
        proof = evidence(source_id="zero-act")
        event = runtime.restore("owl", "network", proof)
        self.assertEqual("maintenance", event.operation)
        self.assertEqual(0, event.amount)
        with self.assertRaisesRegex(MagicRuntimeError, "already applied"):
            runtime.restore("owl", "network", proof)

    def test_one_maintenance_act_can_restore_at_most_once(self):
        runtime = self.runtime(spent=2)
        runtime.claim("bdo", "network", 2)
        runtime.commit("cast-1", "bdo", "network", 2)
        runtime.settle("cast-1")
        proof = evidence(source_id="unique-act")
        runtime.restore("owl", "network", proof)
        with self.assertRaisesRegex(MagicRuntimeError, "already applied"):
            runtime.restore("owl", "network", proof)
        self.assertEqual(1, runtime.spent_total(locality="network"))

    def test_maintenance_requires_role_independent_observer_and_structured_verifier(self):
        runtime = self.runtime()
        with self.assertRaisesRegex(MagicRuntimeError, "Domains Maintainer"):
            runtime.restore("bdo", "network", evidence())
        self_observed = self.runtime(maintenance_observer="owl")
        with self.assertRaisesRegex(MagicRuntimeError, "independent observer"):
            self_observed.restore("owl", "network", evidence())
        no_verifier = MagicRuntime(10, limits(), access_resolver=lambda *_: True, role_resolver=lambda *_: True)
        with self.assertRaisesRegex(MagicRuntimeError, "verifier unavailable"):
            no_verifier.restore("owl", "network", evidence())

    def test_skill_and_cast_evidence_use_same_restoration_path(self):
        for source_kind in ("skill", "cast"):
            runtime = self.runtime(spent=1)
            runtime.claim("bdo", "network", 1)
            runtime.commit("cast-1", "bdo", "network", 1)
            runtime.settle("cast-1")
            event = runtime.restore("owl", "network", evidence(source_kind=source_kind))
            self.assertEqual(source_kind, event.details["evidence"]["source_kind"])
            self.assertEqual(10, runtime.total())

    def test_maintenance_domain_is_exactly_one_of_current_five_domains(self):
        proof = evidence(domain="shadow")
        with self.assertRaisesRegex(MagicRuntimeError, "five repository domains"):
            proof.validate()

    def test_domains_maintainer_can_change_runtime_setting_but_not_conservation_law(self):
        runtime = self.runtime()
        proof = evidence(source_id="config-1", mechanism=MagicRuntime.SETTINGS_MECHANISM)
        event = runtime.configure("owl", {"max_personal": 4, "max_cast": 3}, proof)
        self.assertEqual(4, runtime.limits.max_personal)
        self.assertEqual("configure", event.operation)
        with self.assertRaisesRegex(MagicRuntimeError, "already applied"):
            runtime.configure("owl", {"max_level": 4}, proof)
        with self.assertRaisesRegex(MagicRuntimeError, "total_mana is conserved"):
            runtime.configure("owl", {"total_mana": 11}, evidence(source_id="config-2", mechanism=MagicRuntime.SETTINGS_MECHANISM))

    def test_configuration_requires_exact_runtime_settings_mechanism(self):
        runtime = self.runtime()
        with self.assertRaisesRegex(MagicRuntimeError, "magic-runtime.settings"):
            runtime.configure("owl", {"max_level": 4}, evidence(source_id="config-1", mechanism="some-service"))

    def test_runtime_refuses_setting_change_that_invalidates_live_claim(self):
        runtime = self.runtime()
        runtime.claim("bdo", "network", 3)
        before = runtime.limits
        with self.assertRaisesRegex(MagicRuntimeError, "max_personal"):
            runtime.configure("owl", {"max_personal": 2, "max_cast": 2}, evidence(source_id="config-1", mechanism=MagicRuntime.SETTINGS_MECHANISM))
        self.assertEqual(before, runtime.limits)
        self.assertEqual(3, runtime.claimed_by("bdo"))

    def test_event_details_are_detached_from_caller_and_readers(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "magic.json"
            runtime = self.runtime(path=path)
            changes = {"max_level": 2}
            event = runtime.configure("owl", changes, evidence(source_id="config-alias", mechanism=MagicRuntime.SETTINGS_MECHANISM))
            changes["max_level"] = 1
            event.details["changes"]["max_level"] = 0
            visible = runtime.events[-1]
            visible.details["changes"]["max_level"] = 0
            self.assertEqual(2, runtime.limits.max_level)
            reopened = self.runtime(path=path)
            self.assertEqual(2, reopened.limits.max_level)

    def test_boolean_values_do_not_count_as_integer_runtime_quantities(self):
        with self.assertRaisesRegex(MagicRuntimeError, "non-negative integers"):
            limits(max_level=True).validate(total_mana=10)
        with self.assertRaisesRegex(MagicRuntimeError, "positive integer"):
            MagicRuntime(True, limits())
        runtime = self.runtime()
        with self.assertRaisesRegex(MagicRuntimeError, "positive integer"):
            runtime.claim("bdo", "network", True)
        with self.assertRaisesRegex(MagicRuntimeError, "non-negative integer"):
            runtime.admit_level(True)

    def test_restart_replays_exact_conserved_state_and_maintenance_replay_guard(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "magic.json"
            runtime = self.runtime(path=path, spent=1)
            runtime.claim("bdo", "network", 2)
            runtime.commit("cast-1", "bdo", "network", 1)
            runtime.settle("cast-1")
            proof = evidence(source_id="restore-once")
            runtime.restore("owl", "network", proof)
            reopened = self.runtime(path=path, spent=1)
            self.assertEqual(10, reopened.total())
            self.assertEqual(runtime.sense("bdo", "network", subject="bdo"), reopened.sense("bdo", "network", subject="bdo"))
            self.assertEqual(len(runtime.events), len(reopened.events))
            with self.assertRaisesRegex(MagicRuntimeError, "already applied"):
                reopened.restore("owl", "network", proof)

    def test_tampered_ledger_event_refuses_open(self):
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
