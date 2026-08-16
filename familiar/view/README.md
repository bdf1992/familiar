# Familiar View 0.1

A Familiar View is a bounded representation of one exact accepted Familiar revision for a named perspective, audience, or host.

It is not the Familiar, not a Report, not Presence, and not runtime authority.

```text
Familiar
  -> FamiliarStore.put()
  -> FamiliarRef(id, caster_id, revision, digest)
  -> view policy / perspective
  -> Familiar View
```

## Invariants

```text
Familiar != Familiar View
View != source
View != Report
View != Presence
Omission != absence
Reported advisory authority != runtime authority
```

A View MUST identify the exact `FamiliarRef` it represents. Construct a View only from a Familiar successfully resolved through that reference; otherwise the result is merely attributed guidance, not an exact Familiar View.

A View MAY select, omit, summarize, translate, or rearrange Familiar guidance for a named perspective. It MUST NOT add observations, performance claims, compatibility history, inferred preferences, or other knowledge that is not source Familiar state.

Schema validity does not establish that provenance. A hand-built object can carry any `subject` block it likes. `build_view()` takes a store and a ref and resolves the artifact through it, so a stale, forged, or unretained reference fails before a View exists to be trusted.

Omitted source material remains unknown to the consumer. Omission must not be rewritten as an empty source field.

## Accounting

`omission != absence` only holds if the consumer can tell the two apart. Every source guidance category is therefore accounted for exactly once:

```text
dialect
attention
preferences
stake
advisory_authority
```

Each is either represented in `guidance` or named in `omitted`. A category MUST NOT appear in both, and a View that leaves one unaccounted is invalid. `omitted` is required, so a fully represented View carries an explicit empty array rather than saying nothing at all.

All five are required by `familiar.schema.json`, so a valid Familiar always carries all of them. "The source did not have one" is never an explanation for a gap in a View.

`build_view()` derives `omitted` as the complement of what the caller chose to represent, so a View that silently drops a category cannot be constructed — only hand-assembled, and then validation refuses it naming the category.

## Perspective

A View answers a representation question such as:

- what guidance should this host receive?
- what may be disclosed to this audience?
- what notation or structure is useful in this interaction?

Perspective controls representation, not truth and not authority.

Useful policy names may include `host`, `private`, `shareable`, and `public`, but names alone do not prove disclosure authorization. Environment mechanisms remain responsible for access control.

## View and Presence

A View is knowledge-side material. Possessing or consuming a View does not establish that the Familiar itself is Present in the current Environment.

`Summon Familiar` is the separate effectful operation that establishes bounded session Presence of an independently existing Familiar. A host may consume a View without summoning the Familiar, and a successful summon does not by itself determine which View or disclosure perspective should be used.

```text
Familiar View
    represents an accepted Familiar

Summon Familiar
    makes the accepted Familiar Present
```

A View therefore cannot satisfy `presence-supported` or `target-present`, and it is not evidence that a summon occurred.

## Why this exists

The canonical Familiar should remain small and caster-authored. Hosts often need a bounded representation without receiving the complete private artifact. A Familiar View provides that representation while remaining anchored to an exact accepted revision.

When observations or records later support an account *about* the Familiar, that account is a Report rather than a View. See `../report/README.md`.
