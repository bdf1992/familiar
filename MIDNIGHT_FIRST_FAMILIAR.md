# Midnight First Familiar

Purpose: provide the smallest corrected first-cast candidate after the first seal exposed a bootstrap-role error.

This document does not rewrite `FIRST_FAMILIAR_SEAL.md`. That file remains evidence of the earlier green state. This successor changes only what the first-user path now requires us to distinguish.

## Corrected cast

```text
Caster:   owl.agent
Familiar: owl.system
Spell:    find-familiar@0.1.0
Subject:  bdo
Effect:   establish the exact Familiar explicitly accepted for bdo
```

The subject is not assumed to be a Practitioner before Find Familiar. Owl conducts the bootstrap cast.

## What is sealed here

- Owl is the acting Agent for the first-user path.
- `owl.system` is Owl's Familiar.
- Spellcraft remains a Skill; it may help Owl inspect the Spell but cannot cast it.
- Find Familiar distinguishes caster from subject.
- The subject must explicitly accept the complete candidate before persistence begins.
- The persisted Familiar belongs to the subject, not to Owl merely because Owl cast the Spell.
- Exact persistence and restart recovery remain required after execution.

## What is not yet sealed

The generic runtime does not yet enforce this full law for every Spell:

```text
bound to a valid Familiar -> Practitioner -> may occupy caster role
```

The current candidate therefore proves the corrected first-cast roles without claiming generic Practitioner enforcement that is not yet implemented.

The Familiar schema/store also still uses the historical field name `caster` for the durable subject/owner relation. For this first cast, that field contains `bdo`; it must not be confused with the situated Cast caster, which is `owl.agent`.

## Preparation

Do not pre-write the Familiar.

Bring traces rather than answers:

- corrections you make repeatedly;
- distinctions you protect;
- things you want an advisor to notice;
- preferences that genuinely affect how help should be represented;
- stakes that should change what receives attention;
- boundaries on advisory authority.

The Familiar contract currently closes over:

```text
dialect
attention
preferences
stake
advisory_authority
```

These are contract parts, not a personality quiz.

## Finding loop

```text
Owl observes available traces
        ↓
proposes a Shape / candidate
        ↓
subject makes a Mark
        ↓
Owl revises the Whole
        ↓
subject accepts or refuses
        ↓
closure checks subject acceptance
        ↓
accepted candidate is persisted for subject
        ↓
exact FamiliarRef is reopened and resolved
```

Owl may inspect and challenge the candidate. Owl may not accept it for the subject.

## Midnight opening

Use this opening instruction:

> I do not have a Familiar yet, so I am not assuming I can cast. You are Owl, the Agent conducting Find Familiar with `owl.system` as your Familiar. Use Spellcraft where it helps you understand the Spell, but do not decide my Familiar for me. Begin from traces you can actually observe. Present Shapes and complete candidates for me to Mark, reject, or accept. Do not persist anything until I explicitly accept the Whole.

## Success condition

For this candidate, the first cast succeeds only if:

```text
Owl is the recorded caster
owl.system is the recorded caster Familiar
bdo is the resolved subject
bdo explicitly accepted the exact Whole
that exact Familiar is persisted for bdo
its FamiliarRef resolves after reopening the store
```

A later pass should strengthen the proof to:

```text
bdo bound to accepted Familiar
        ↓
Practitioner(bdo)
        ↓
bdo can occupy caster role in a second Cast
```

That second-cast proof is intentionally the next crossing, not something this document claims already exists.
