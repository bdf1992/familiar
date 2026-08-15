from __future__ import annotations

import unittest

from presence import PresenceError, PresenceStore


class Presence05Tests(unittest.TestCase):
    def test_session_presence_survives_establish_until_context_release(self):
        objects = {"owl.system": {"id": "owl.system", "caster": {"id": "agent-spells", "kind": "system"}}}
        store = PresenceStore(lambda ref: objects.get(ref))
        self.assertTrue(store.exists("owl.system"))
        self.assertFalse(store.present("owl.system", "session-1"))
        store.establish("owl.system", "session-1", lifetime="session", cast_id="cast-1")
        self.assertTrue(store.present("owl.system", "session-1"))
        self.assertEqual("owl.system", store.resolve("owl.system", "session-1")["id"])
        store.release_context("session-1")
        self.assertFalse(store.present("owl.system", "session-1"))
        self.assertTrue(store.exists("owl.system"))

    def test_presence_detects_identity_mutation(self):
        objects = {"owl.system": {"id": "owl.system", "caster": {"id": "agent-spells", "kind": "system"}}}
        store = PresenceStore(lambda ref: objects.get(ref))
        store.establish("owl.system", "session-1", lifetime="session", cast_id="cast-1")
        objects["owl.system"]["caster"]["id"] = "someone-else"
        with self.assertRaises(PresenceError):
            store.resolve("owl.system", "session-1")

    def test_only_session_lifetime_is_supported(self):
        store = PresenceStore(lambda ref: {"id": ref})
        with self.assertRaises(PresenceError):
            store.establish("owl.system", "session-1", lifetime="forever", cast_id="cast-1")


if __name__ == "__main__":
    unittest.main()
