# First Familiar Seal

Seal purpose: freeze the smallest local-first Agent Spells surface trusted for the practitioner's first real `Find Familiar` cast.

This seal is not a universal release, reliability grade, or claim that all candidate protocol work is Current. It is a bounded readiness statement for one practitioner, one local environment, and one Spell Effect.

## Intended cast

```text
Spell:  find-familiar@0.1.0
Effect: establish
Caster: explicitly resolved human practitioner
Result: one schema-valid, explicitly accepted, restart-safe Familiar artifact + FamiliarRef
```

## Trusted boundary

The first cast may rely on:

- the five-domain distinctions in `FOUNDATIONS.md`;
- `familiar/familiar.schema.json` as the Familiar structural contract;
- Familiar-owned validation;
- `familiar/find-familiar/SKILL.md` as the authoring/inspection technique;
- canonical `owl.system` as an optional protocol-aware advisor;
- the `find-familiar@0.1.0` candidate declaration and exact Technique Binding;
- the invariant current Cast path plus candidate/binding adapters exercised by the tests;
- restart-safe `FamiliarStore(root)` for the Effect artifact;
- restart-safe `LocalRegistry(root)` for private personal Spellbook storage when desired;
- the host account/filesystem as the local confidentiality and access-control boundary.

## Closure law

The cast must fail closed unless all before Requirements are satisfied.

For Find Familiar:

1. **caster-resolved** — the caster is explicit, not inferred from prose or history;
2. **familiar-store-supported** — the active environment exposes an exact persistent Familiar store;
3. **caster-accepted** — the practitioner has explicitly accepted the complete candidate that will be persisted.

Only then may effectful persistence begin.

After execution:

1. **familiar-valid** — the persisted artifact validates against the Familiar contract;
2. **familiar-persisted** — the exact accepted artifact resolves from the returned `FamiliarRef`.

If either after Requirement fails, the Effect does not count as resolved and the residual must remain visible.

## Practitioner preparation

You do **not** need to pre-write your Familiar.

Bring:

- an explicit caster identity/reference for this local protocol;
- a few genuine traces: things you want help noticing, preserving, challenging, or representing;
- willingness to reject candidate interpretations that do not feel structurally true;
- willingness to explicitly accept one complete candidate when it finally reconstructs what you mean.

Useful traces can be corrections, preferences, stakes, recurring failures, ways of speaking, or boundaries on what an advisor may do.

The five Familiar Parts are:

```text
dialect
attention
preferences
stake
advisory_authority
```

These are not questionnaire answers that the system should force. They are the contract dimensions into which accepted evidence eventually closes.

## Finding loop

```text
Point
  -> give Owl / Find Familiar a trace

Shape
  -> receive a substantive reading you can recognize or reject

Mark
  -> correct, reject, refine, or add evidence

Pass
  -> receive a new complete candidate

Whole
  -> inspect all five Familiar Parts together

Accept
  -> explicitly select this exact complete candidate

Close
  -> runtime checks before Requirements

Establish
  -> persist exact candidate

Observe
  -> validate + resolve FamiliarRef

Resolved
  -> only if the exact accepted Familiar can be recovered
```

Owl may say "this appears to be a recurring preference" or "this candidate is leaking persona into authority." Owl may not decide "this is who you are" or accept the Whole for you.

## Recommended local data layout

Keep personal runtime state out of the public source repository.

```text
AgentSpells/
  registry/
    books/
  familiars/
```

Suggested host roots:

```text
Windows: %LOCALAPPDATA%\AgentSpells\
Unix:    ${XDG_DATA_HOME:-~/.local/share}/agent-spells/
```

For temporary repository-local development only:

```text
.agent-spells-local/
```

That path is ignored by Git in this seal.

## Security statement

This seal provides local durability and integrity detection, not a full cryptographic identity system.

- atomic writes reduce partial-write corruption;
- hashed filenames prevent raw artifact IDs from becoming paths;
- SHA-256 digests make mutation noticeable;
- POSIX permissions are tightened where supported;
- host account controls / disk encryption provide local confidentiality.

Deferred: issuer signatures, trust chains, remote publication/discovery security.

## Evidence required for the seal

Before using the seal, the branch must have a successful complete CI run including:

- Find Familiar accepted-candidate end-to-end persistence;
- unaccepted-candidate refusal before executor entry;
- Familiar restart recovery;
- Familiar tamper detection;
- personal Spellbook restart recovery;
- Spellbook tamper detection;
- existing Cast, Registry, Presence, Summon Owl, and workspace-tidy regressions.

## Residuals intentionally carried past the seal

These do not block the first local Find Familiar cast:

- issuer signatures / trust chains;
- remote Library transport and subscription polling;
- semantic-version ranges;
- Presence lifetimes beyond session;
- Dismiss Spell;
- wider reliability / standing classifications;
- cleanup of older Work/draft lifecycle surfaces.

## Midnight procedure

Immediately before the cast:

1. use the exact sealed commit/branch;
2. confirm the full CI run is green;
3. choose the local FamiliarStore root;
4. resolve the caster explicitly;
5. begin with practitioner-authored traces rather than a prefilled Familiar;
6. let Owl inspect candidate quality and boundaries;
7. make Marks until the complete candidate is recognizable;
8. inspect `dialect`, `attention`, `preferences`, `stake`, and `advisory_authority` together;
9. explicitly accept or refuse the Whole;
10. if accepted, let closure run and persist it;
11. resolve the returned `FamiliarRef` from a reopened store;
12. preserve the resulting CAST record and FamiliarRef as evidence of the first successful Effect.

The meaningful moment is not the clock. The meaningful crossing is:

```text
provisional candidate
    -> explicit practitioner acceptance
    -> closed cast
    -> persisted Familiar
    -> independently resolved exact artifact
```

That is the first Familiar seal.
