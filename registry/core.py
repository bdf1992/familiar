from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any

import yaml


class RegistryError(ValueError):
    """A declaration cannot be safely registered or resolved."""


def _digest(text: str) -> str:
    return "sha256:" + sha256(text.encode("utf-8")).hexdigest()


def _frontmatter_identity(spell_text: str) -> tuple[str, str]:
    if not spell_text.startswith("---\n"):
        raise RegistryError("SPELL.md must begin with YAML frontmatter")
    end = spell_text.find("\n---", 4)
    if end < 0:
        raise RegistryError("SPELL.md frontmatter is not closed")
    data = yaml.safe_load(spell_text[4:end])
    if not isinstance(data, dict):
        raise RegistryError("SPELL.md frontmatter must be a mapping")
    name = data.get("name")
    version = data.get("version")
    if not isinstance(name, str) or not name:
        raise RegistryError("SPELL.md name is required")
    if not isinstance(version, str) or not version:
        raise RegistryError("SPELL.md version is required")
    return name, version


@dataclass(frozen=True)
class Scroll:
    id: str
    spell: str
    version: str
    digest: str
    issuer: str | None = None

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Scroll":
        carries = value.get("carries") or {}
        source = value.get("source") or {}
        if value.get("scroll_format") != "0.1":
            raise RegistryError("unsupported scroll_format")
        return cls(
            id=value["id"],
            spell=carries["spell"],
            version=carries["version"],
            digest=carries["digest"],
            issuer=source.get("issuer"),
        )

    def verify(self, spell_text: str) -> None:
        name, version = _frontmatter_identity(spell_text)
        if name != self.spell or version != self.version:
            raise RegistryError("scroll identity does not match SPELL.md")
        actual = _digest(spell_text)
        if actual != self.digest:
            raise RegistryError("scroll digest does not match SPELL.md")


def seal_scroll(spell_text: str, *, scroll_id: str, issuer: str | None = None) -> dict[str, Any]:
    """Create a non-executable carrier for one exact Spell declaration."""
    name, version = _frontmatter_identity(spell_text)
    value: dict[str, Any] = {
        "scroll_format": "0.1",
        "id": scroll_id,
        "carries": {"spell": name, "version": version, "digest": _digest(spell_text)},
    }
    if issuer is not None:
        value["source"] = {"issuer": issuer}
    return value


@dataclass(frozen=True)
class Registration:
    spell: str
    version: str
    digest: str
    source_scroll: str
    issuer: str | None
    declaration: str


@dataclass(frozen=True)
class ResolvedSpell:
    spell: str
    version: str
    digest: str
    declaration: str
    book: str
    library: str | None = None
    provenance: tuple[str, ...] = ()


@dataclass
class Spellbook:
    id: str
    _entries: dict[tuple[str, str], Registration] = field(default_factory=dict, init=False, repr=False)

    def register(self, scroll: Scroll, spell_text: str) -> Registration:
        scroll.verify(spell_text)
        key = (scroll.spell, scroll.version)
        existing = self._entries.get(key)
        if existing is not None:
            if existing.digest != scroll.digest:
                raise RegistryError("same spell name/version has a different digest")
            return existing
        registration = Registration(
            spell=scroll.spell,
            version=scroll.version,
            digest=scroll.digest,
            source_scroll=scroll.id,
            issuer=scroll.issuer,
            declaration=spell_text,
        )
        self._entries[key] = registration
        return registration

    def resolve(self, spell: str, version: str) -> ResolvedSpell:
        registration = self._entries.get((spell, version))
        if registration is None:
            raise RegistryError(f"spell not registered: {spell}@{version}")
        return ResolvedSpell(
            spell=spell,
            version=version,
            digest=registration.digest,
            declaration=registration.declaration,
            book=self.id,
            provenance=(f"scroll:{registration.source_scroll}",),
        )

    def list(self) -> tuple[Registration, ...]:
        return tuple(self._entries[key] for key in sorted(self._entries))


_RELATIONS = {"issues", "publishes", "subscribes_to", "consumes_from"}


@dataclass(frozen=True)
class LibraryRelation:
    subject: str
    relation: str
    object: str

    def __post_init__(self) -> None:
        if self.relation not in _RELATIONS:
            raise RegistryError(f"unsupported library relation: {self.relation}")


@dataclass
class Library:
    id: str
    _books: dict[str, Spellbook] = field(default_factory=dict, init=False, repr=False)
    _relations: list[LibraryRelation] = field(default_factory=list, init=False, repr=False)

    def register_book(self, book: Spellbook) -> None:
        existing = self._books.get(book.id)
        if existing is not None and existing is not book:
            raise RegistryError(f"book id already registered: {book.id}")
        self._books[book.id] = book

    def relate(self, subject: str, relation: str, object: str) -> LibraryRelation:
        edge = LibraryRelation(subject=subject, relation=relation, object=object)
        if edge not in self._relations:
            self._relations.append(edge)
        return edge

    def relations(self) -> tuple[LibraryRelation, ...]:
        return tuple(self._relations)

    def resolve(self, book_id: str, spell: str, version: str) -> ResolvedSpell:
        book = self._books.get(book_id)
        if book is None:
            raise RegistryError(f"book not registered: {book_id}")
        resolved = book.resolve(spell, version)
        return ResolvedSpell(
            spell=resolved.spell,
            version=resolved.version,
            digest=resolved.digest,
            declaration=resolved.declaration,
            book=resolved.book,
            library=self.id,
            provenance=resolved.provenance + (f"book:{book_id}", f"library:{self.id}"),
        )
