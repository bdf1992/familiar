# Familiar View 0.1

A Familiar View is a bounded representation of one exact accepted Familiar revision for a named perspective, audience, or host.

It is not the Familiar, not a Report, and not runtime authority.

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
Omission != absence
Reported advisory authority != runtime authority
```

A View MUST identify the exact `FamiliarRef` it represents. Construct a View only from a Familiar successfully resolved through that reference; otherwise the result is merely attributed guidance, not an exact Familiar View.

A View MAY select, omit, summarize, translate, or rearrange Familiar guidance for a named perspective. It MUST NOT add observations, performance claims, compatibility history, inferred preferences, or other knowledge that is not source Familiar state.

Omitted source material remains unknown to the consumer. Omission must not be rewritten as an empty source field.

## Perspective

A View answers a representation question such as:

- what guidance should this host receive?
- what may be disclosed to this audience?
- what notation or structure is useful in this interaction?

Perspective controls representation, not truth and not authority.

Useful policy names may include `host`, `private`, `shareable`, and `public`, but names alone do not prove disclosure authorization. Environment mechanisms remain responsible for access control.

## Why this exists

The canonical Familiar should remain small and caster-authored. Hosts often need a bounded representation without receiving the complete private artifact. A Familiar View provides that representation while remaining anchored to an exact accepted revision.

When observations or records later support an account *about* the Familiar, that account is a Report rather than a View. See `../report/README.md`.
