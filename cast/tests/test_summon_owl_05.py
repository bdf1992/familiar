from __future__ import annotations

from copy import deepcopy
import json
import unittest
from pathlib import Path

from kernel.resources import OWL_PATH
from kernel.spell_kernel import SpellKernel, validate_familiar
from presence import PresenceStore
from registry import Library, Scroll, Spellbook
from validation.candidate_adapter import load_candidate_spell
from validation.casting_04 import cast_with_binding, validate_technique_binding

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "summon-familiar"


class SummonOwl05Tests(unittest.TestCase):
    def setUp(self):
        self.spell_text = (EXAMPLE / "SPELL.md").read_text(encoding="utf-8")
        self.scroll = Scroll.from_dict(json.loads((EXAMPLE / "SCROLL.json").read_text(encoding="utf-8")))
        self.binding = json.loads((EXAMPLE / "binding.json").read_text(encoding="utf-8"))
        validate_technique_binding(self.binding)
        self.owl_text = OWL_PATH.read_text(encoding="utf-8")
        self.owl = json.loads(self.owl_text)
        self.owl_before = deepcopy(self.owl)

    def _resolve_registered_spell(self):
        book = Spellbook("agent-spells.core")
        book.register(self.scroll, self.spell_text)
        library = Library("agent-spells.library")
        library.register_book(book)
        resolved = library.resolve(book.id, "summon-familiar", "0.1.0")
        spell = load_candidate_spell(EXAMPLE / "SPELL.md")
        self.assertEqual(self.scroll.digest, resolved.digest)
        return spell

    def _kernel(self, store: PresenceStore, actions: list[str]):
        def ref(context):
            return (context.get("target") or {}).get("ref")

        def session(context):
            return (context.get("target") or {}).get("context")

        def target_exists(phase, context):
            return store.exists(ref(context))

        def target_is_familiar(phase, context):
            value = store.lookup(ref(context))
            if value is None:
                return False
            try:
                validate_familiar(value)
            except Exception:
                return False
            return True

        def target_identity_resolved(phase, context):
            value = store.lookup(ref(context))
            return value is not None and value.get("id") == ref(context)

        def presence_supported(phase, context):
            return isinstance(store, PresenceStore) and bool(session(context))

        def target_present(phase, context):
            return store.present(ref(context), session(context))

        def identity_preserved(phase, context):
            value = store.lookup(ref(context))
            return value == self.owl_before

        def execute(spell, effect_id, context, execution_max_ms):
            actions.append("executor-entered")
            target = context["target"]
            record = store.establish(target["ref"], target["context"], lifetime="session", cast_id="cast-summon-owl")
            return {"presence": {"target": record.target_ref, "context": record.context_id, "lifetime": record.lifetime}}

        return SpellKernel(
            requirements={
                "target-exists": target_exists,
                "target-is-familiar": target_is_familiar,
                "target-identity-resolved": target_identity_resolved,
                "presence-supported": presence_supported,
                "target-present": target_present,
                "identity-preserved": identity_preserved,
            },
            executor=execute,
        )

    def test_registered_spell_summons_canonical_owl_for_session(self):
        spell = self._resolve_registered_spell()
        store = PresenceStore(lambda ref: self.owl if ref == "owl.system" else None)
        actions = []
        self.assertFalse(store.present("owl.system", "session-1"))
        record = cast_with_binding(
            self._kernel(store, actions),
            spell,
            self.binding,
            effect_id="summon",
            caster={"id": "bdo", "kind": "human"},
            target={"ref": "owl.system", "context": "session-1"},
            cast_id="cast-summon-owl",
        )
        self.assertEqual("closed", record["closure"]["decision"])
        self.assertEqual("resolved", record["outcome"])
        self.assertEqual(["executor-entered"], actions)
        self.assertTrue(store.present("owl.system", "session-1"))
        self.assertEqual("owl.system", store.resolve("owl.system", "session-1")["id"])
        self.assertEqual(self.owl_before, self.owl)
        self.assertEqual(self.owl_text, OWL_PATH.read_text(encoding="utf-8"))
        store.release_context("session-1")
        self.assertFalse(store.present("owl.system", "session-1"))
        self.assertTrue(store.exists("owl.system"))

    def test_missing_owl_refuses_before_executor(self):
        spell = self._resolve_registered_spell()
        store = PresenceStore(lambda ref: None)
        actions = []
        record = cast_with_binding(
            self._kernel(store, actions),
            spell,
            self.binding,
            effect_id="summon",
            caster={"id": "bdo", "kind": "human"},
            target={"ref": "owl.system", "context": "session-1"},
        )
        self.assertEqual("refused", record["closure"]["decision"])
        self.assertEqual([], actions)
        self.assertTrue(any("target-exists" in reason for reason in record["closure"]["reasons"]))

    def test_owl_like_fabrication_without_presence_cannot_resolve(self):
        spell = self._resolve_registered_spell()
        store = PresenceStore(lambda ref: self.owl if ref == "owl.system" else None)

        def fake_execute(spell, effect_id, context, execution_max_ms):
            return {"owl_like_copy": deepcopy(self.owl)}

        kernel = self._kernel(store, [])
        kernel.executor = fake_execute
        record = cast_with_binding(
            kernel,
            spell,
            self.binding,
            effect_id="summon",
            caster={"id": "bdo", "kind": "human"},
            target={"ref": "owl.system", "context": "session-1"},
        )
        self.assertNotEqual("resolved", record["outcome"])
        self.assertFalse(store.present("owl.system", "session-1"))


if __name__ == "__main__":
    unittest.main()
