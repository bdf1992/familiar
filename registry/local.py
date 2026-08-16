from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
from typing import Any

from .core import RegistryError, Scroll, Spellbook


def _file_key(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest() + ".json"


def _atomic_json_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.parent.chmod(0o700)
    except OSError:
        pass
    fd, tmp_name = tempfile.mkstemp(prefix=".tmp-", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, sort_keys=True, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.chmod(tmp_name, 0o600)
        except OSError:
            pass
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


class LocalRegistry:
    """Filesystem persistence adapter for existing Registry objects.

    This is registration storage, not publication. It does not add remote
    discovery, trust chains, signing, or casting authority.
    """

    def __init__(self, root: str | Path):
        self.root = Path(root).expanduser().resolve()
        self.books = self.root / "books"
        self.books.mkdir(parents=True, exist_ok=True)
        try:
            self.root.chmod(0o700)
            self.books.chmod(0o700)
        except OSError:
            pass

    def _book_path(self, book_id: str) -> Path:
        return self.books / _file_key(book_id)

    def save_book(self, book: Spellbook) -> None:
        entries = []
        for registration in book.list():
            entries.append(
                {
                    "spell": registration.spell,
                    "version": registration.version,
                    "digest": registration.digest,
                    "source_scroll": registration.source_scroll,
                    "issuer": registration.issuer,
                    "declaration": registration.declaration,
                }
            )
        _atomic_json_write(
            self._book_path(book.id),
            {"local_registry_format": "0.1", "book": book.id, "entries": entries},
        )

    def open_book(self, book_id: str) -> Spellbook:
        path = self._book_path(book_id)
        book = Spellbook(book_id)
        if not path.exists():
            return book
        try:
            envelope = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RegistryError(f"cannot read local Spellbook: {book_id}") from exc
        if envelope.get("local_registry_format") != "0.1" or envelope.get("book") != book_id:
            raise RegistryError("local Spellbook envelope does not match requested book")
        entries = envelope.get("entries")
        if not isinstance(entries, list):
            raise RegistryError("local Spellbook entries must be a list")
        for item in entries:
            if not isinstance(item, dict):
                raise RegistryError("local Spellbook entry must be an object")
            scroll = Scroll(
                id=item["source_scroll"],
                spell=item["spell"],
                version=item["version"],
                digest=item["digest"],
                issuer=item.get("issuer"),
            )
            book.register(scroll, item["declaration"])
        return book

    def register(self, book_id: str, scroll: Scroll, spell_text: str):
        book = self.open_book(book_id)
        registration = book.register(scroll, spell_text)
        self.save_book(book)
        return registration

    def resolve(self, book_id: str, spell: str, version: str):
        return self.open_book(book_id).resolve(spell, version)
