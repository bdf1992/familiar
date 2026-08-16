# Familiar Report 0.1

A Familiar Report is a bounded projection of one exact `FamiliarRef` for a particular audience or host.

It is not the Familiar, not a replacement persistence format, and not runtime authority.

```text
Familiar
  -> FamiliarStore.put()
  -> FamiliarRef(id, caster_id, revision, digest)
  -> report policy
  -> Familiar Report
```

## Invariants

```text
Familiar != Familiar Report
Projection != source
Omission != absence
Claim != observation
Reported advisory authority != runtime authority
```

A report MUST identify the exact Familiar revision it describes. If the source artifact cannot be resolved and its digest verified, `subject_digest_verified` must be false and the report must not claim to be an exact projection.

A report MAY omit or summarize Familiar material according to a named projection policy. Omitted material stays unknown to the consumer; omission must never be rewritten as an empty source field.

A report MAY include observations or claims derived from work history, CAST records, host evidence, or other attributable sources. Those are report evidence, not Familiar state. A claim must preserve whether it is merely asserted, supported, defeated, or unknown.

A report MUST remain advisory. It cannot satisfy a Spell Requirement, grant authority, waive a limit, change an Effect, or determine CAST outcome.

## Projection policies

Policy names are host- or practitioner-defined in 0.1. Useful examples include:

- `private` — owner-authorized projection;
- `host` — guidance needed by a specific agent host;
- `shareable` — collaboration guidance with private stake omitted;
- `public` — safe identity/high-level guidance only;
- `diagnostic` — compatibility, corrections, evidence, and defeated claims.

The policy name does not itself prove that disclosure was authorized. The host or calling procedure remains responsible for authorization until a concrete Environment mechanism is bound.

## Why this is separate

The Familiar contract should stay small and caster-authored. Skills, capability scores, compatibility history, host configuration, and runtime evidence do not belong in the Familiar merely because they are useful to report.

Reports let those facts evolve independently while remaining anchored to an exact accepted Familiar revision.
