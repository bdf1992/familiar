from __future__ import annotations

import unittest

from familiar.store import FamiliarStore, FamiliarStoreError
from practitioner import CapabilityReceipt, CastSession, CastSessionError, Situation, compile_cast_plan


def candidate():
    return {
        "familiar_format": "0.3",
        "id": "bdo.familiar",
        "caster": {"id": "bdo", "kind": "human"},
        "dialect": {"description": "Compact distinction-first working language."},
        "attention": ["collapsed distinctions"],
        "preferences": ["small inspectable kernels"],
        "stake": ["practitioner agent work"],
        "advisory_authority": [],
    }


class Practitioner05Tests(unittest.TestCase):
    def test_draw_loop_is_preclosure_until_acceptance(self):
        session = CastSession("cast-find-1", "find-familiar", "establish", {"id": "bdo", "kind": "human"}, {"caster": "bdo"})
        session.begin_preparation()
        session.propose(candidate())
        self.assertEqual("awaiting_mark", session.state)
        self.assertIsNone(session.accepted)
        session.mark("notice conceptual drift too")
        revised = candidate()
        revised["attention"].append("conceptual drift")
        session.propose(revised)
        accepted = session.accept()
        self.assertEqual("ready_to_close", session.state)
        self.assertEqual(revised, accepted)
        session.close()
        self.assertEqual("closed", session.state)

    def test_cannot_close_before_practitioner_accepts(self):
        session = CastSession("cast-find-1", "find-familiar", "establish", {"id": "bdo", "kind": "human"}, None)
        session.begin_preparation()
        session.propose(candidate())
        with self.assertRaises(CastSessionError):
            session.close()

    def test_familiar_store_persists_exact_accepted_artifact(self):
        store = FamiliarStore()
        ref = store.put(candidate(), caster_id="bdo")
        resolved = store.resolve(ref)
        self.assertEqual(candidate(), resolved)
        resolved["attention"].append("local mutation")
        self.assertEqual(candidate(), store.resolve(ref))

    def test_familiar_store_rejects_wrong_owner(self):
        store = FamiliarStore()
        with self.assertRaises(FamiliarStoreError):
            store.put(candidate(), caster_id="other")

    def test_situation_binds_requirements_to_real_capability_receipts(self):
        receipts = (
            CapabilityReceipt("familiar persistence", "local", ("resolve", "write"), "available", "bdo", "familiar-store", "probe:ok"),
            CapabilityReceipt("practitioner interaction", "chat", ("observe",), "available", "bdo", "chat-session", "host-event"),
        )
        situation = Situation("situation-1", "session-1", {"id": "bdo", "kind": "human"}, {"caster": "bdo"}, ("local", "chat"), receipts, ("owl.system",))
        plan = compile_cast_plan({"familiar-store-supported": "write", "caster-accepted": "observe"}, situation)
        self.assertTrue(plan.ready)
        self.assertEqual("local", plan.requirements["familiar-store-supported"].environment)

    def test_situation_reports_missing_enforcement_mechanism(self):
        situation = Situation("situation-1", "session-1", {"id": "bdo", "kind": "human"}, None)
        plan = compile_cast_plan({"familiar-store-supported": "write"}, situation)
        self.assertFalse(plan.ready)
        self.assertEqual(("capability-missing:familiar-store-supported:write",), plan.gaps)


if __name__ == "__main__":
    unittest.main()
