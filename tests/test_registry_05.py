from __future__ import annotations

import json
import unittest
from pathlib import Path

from registry import Library, RegistryError, Scroll, Spellbook, seal_scroll

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "summon-familiar"


class Registry05Tests(unittest.TestCase):
    def setUp(self):
        self.spell_text = (EXAMPLE / "SPELL.md").read_text(encoding="utf-8")
        self.scroll = Scroll.from_dict(json.loads((EXAMPLE / "SCROLL.json").read_text(encoding="utf-8")))

    def test_seal_matches_canonical_scroll(self):
        sealed = seal_scroll(self.spell_text, scroll_id=self.scroll.id, issuer="agent-spells")
        self.assertEqual(self.scroll.digest, sealed["carries"]["digest"])

    def test_scroll_registers_without_casting_surface(self):
        book = Spellbook("bdo.personal")
        registration = book.register(self.scroll, self.spell_text)
        self.assertEqual("summon-familiar", registration.spell)
        self.assertFalse(hasattr(self.scroll, "cast"))
        self.assertFalse(hasattr(book, "cast"))

    def test_digest_mismatch_refuses_registration(self):
        book = Spellbook("bdo.personal")
        with self.assertRaises(RegistryError):
            book.register(self.scroll, self.spell_text + "\nmutated")
        self.assertEqual((), book.list())

    def test_same_name_version_different_digest_conflicts(self):
        book = Spellbook("bdo.personal")
        book.register(self.scroll, self.spell_text)
        other = Scroll(self.scroll.id + "-other", self.scroll.spell, self.scroll.version, "sha256:" + "0" * 64, self.scroll.issuer)
        with self.assertRaises(RegistryError):
            book.register(other, self.spell_text)

    def test_library_resolves_exact_spell_with_provenance(self):
        book = Spellbook("bdo.personal")
        book.register(self.scroll, self.spell_text)
        library = Library("bdo.local")
        library.register_book(book)
        library.relate("agent-spells", "issues", book.id)
        library.relate(library.id, "consumes_from", book.id)
        resolved = library.resolve(book.id, "summon-familiar", "0.1.0")
        self.assertEqual(self.scroll.digest, resolved.digest)
        self.assertEqual("bdo.local", resolved.library)
        self.assertIn("library:bdo.local", resolved.provenance)


if __name__ == "__main__":
    unittest.main()
