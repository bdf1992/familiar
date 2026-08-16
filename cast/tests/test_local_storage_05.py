from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from familiar.store import FamiliarStore, FamiliarStoreError
from registry import LocalRegistry, RegistryError, Scroll, seal_scroll

ROOT = Path(__file__).resolve().parents[1]
SUMMON = ROOT / "examples" / "summon-familiar" / "SPELL.md"


def familiar_candidate():
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


class LocalStorage05Tests(unittest.TestCase):
    def test_familiar_survives_store_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "familiars"
            ref = FamiliarStore(root).put(familiar_candidate(), caster_id="bdo")
            resolved = FamiliarStore(root).resolve(ref)
            self.assertEqual(familiar_candidate(), resolved)

    def test_familiar_tamper_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "familiars"
            store = FamiliarStore(root)
            ref = store.put(familiar_candidate(), caster_id="bdo")
            [path] = list(root.glob("*.json"))
            envelope = json.loads(path.read_text(encoding="utf-8"))
            envelope["familiar"]["attention"].append("tampered")
            path.write_text(json.dumps(envelope), encoding="utf-8")
            with self.assertRaises(FamiliarStoreError):
                FamiliarStore(root).resolve(ref)

    def test_spellbook_survives_registry_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            spell_text = SUMMON.read_text(encoding="utf-8")
            sealed = seal_scroll(spell_text, scroll_id="summon-familiar-0.1.0", issuer="agent-spells")
            scroll = Scroll.from_dict(sealed)
            LocalRegistry(tmp).register("bdo.personal", scroll, spell_text)
            resolved = LocalRegistry(tmp).resolve("bdo.personal", "summon-familiar", "0.1.0")
            self.assertEqual(scroll.digest, resolved.digest)
            self.assertEqual(spell_text, resolved.declaration)

    def test_spellbook_tamper_is_detected_on_reopen(self):
        with tempfile.TemporaryDirectory() as tmp:
            spell_text = SUMMON.read_text(encoding="utf-8")
            scroll = Scroll.from_dict(seal_scroll(spell_text, scroll_id="summon-familiar-0.1.0"))
            registry = LocalRegistry(tmp)
            registry.register("bdo.personal", scroll, spell_text)
            [path] = list((Path(tmp) / "books").glob("*.json"))
            envelope = json.loads(path.read_text(encoding="utf-8"))
            envelope["entries"][0]["declaration"] += "\nmutated"
            path.write_text(json.dumps(envelope), encoding="utf-8")
            with self.assertRaises(RegistryError):
                LocalRegistry(tmp).open_book("bdo.personal")


if __name__ == "__main__":
    unittest.main()
