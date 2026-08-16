# Agent Spells

Agent Spells is an experimental local-first protocol for declaring **Spells**, attempting their **Effects** through one invariant casting law, preserving exact runtime evidence as **CAST** records, and keeping Familiar guidance distinct from runtime authority.

The repository is organized around five subject domains:

- **Spell** — portable Effect declarations, Requirements, Telemetry, and Spellcraft.
- **Cast** — situated invocation, closure, governed execution, observation, residuals, and CAST records.
- **Familiar** — dialect, attention, preferences, stake, advisory authority, validation, and persistence.
- **Registry** — Scrolls, Spellbooks, Libraries, exact resolution, provenance, and local registration storage.
- **Environment** — concrete host mechanisms such as Presence, observability, authority, scope, meters, clocks, and containment.

The root is the assembly over those domains. See [FOUNDATIONS.md](FOUNDATIONS.md) for the distinctions that must survive composition.

## Core law

```text
Spell != Cast
Knowledge != Consequence
Identity != Presence
Meaning != Expression
Effect != Technique
Requirement != Assertion
Registration != Publication
Familiar guidance != Runtime authority
```

A Spell declares a possible Effect and the Requirements under which it may count. A Cast is one situated attempt. Scrolls, Spellbooks, Libraries, registration, publication, and resolution may change knowledge or addressability; only casting may attempt an Effect.

For the current bootstrap work, one additional relation matters:

```text
bound to a valid Familiar -> Practitioner
```

`Practitioner` is a derived condition, not a durable type. `Caster` is the role a Practitioner occupies in one Cast.

## First Familiar path

The intended first-user path is now:

```text
owl.agent + owl.system
    -> Owl is the acting Agent with its system Familiar

Owl casts find-familiar@0.1.0 for an unbound subject
    -> prepare complete Familiar candidates
    -> subject Marks / corrections
    -> subject explicitly accepts one complete candidate
    -> closure
    -> persist the exact accepted Familiar for that subject
    -> return FamiliarRef

Resolve FamiliarRef after restart
    -> exact accepted Familiar is recovered
```

The current executable proof now uses `owl.agent` as the caster and `owl.system` as Owl's Familiar. The subject whose Familiar is being found is **not** treated as the caster merely to bootstrap the protocol.

`subject-accepted` is a **before Requirement** for Find Familiar: persistence may not begin until the subject has accepted the complete candidate.

### Important current boundary

This branch proves the corrected first-cast roles, but it does **not yet** claim that the generic Cast runtime enforces the full relation-derived practitioner law for every Spell. Generic binding resolution and fail-closed `Practitioner` enforcement remain the next runtime hardening step.

That residual is intentionally visible rather than hidden behind a special-case claim.

## Owl, Spellcraft, and Find Familiar

These are different responsibilities:

```text
Owl            = Agent conducting the bootstrap interaction
owl.system     = Owl's Familiar
Spellcraft     = Skill for understanding / inspecting / repairing Spell declarations
Find Familiar  = Spell whose first-user path establishes the accepted Familiar for the subject
Technique      = interactive drawing / preparation used to reach an accepted Whole
SpellCast      = runtime that closes, executes, observes, and records the Cast
```

Spellcraft does not cast Spells. Owl can use Spellcraft while conducting Find Familiar.

## Local-first storage

A personal Spellbook does **not** need to be published.

- `registry.LocalRegistry(root)` persists existing `Spellbook` objects and re-verifies exact declarations when reopened.
- `familiar.FamiliarStore(root)` persists exact Familiar artifacts and resolves them by revision + digest.
- Writes use atomic replacement; IDs are hashed before becoming filenames; private POSIX permissions are applied where supported.
- The host filesystem remains the confidentiality/access-control boundary. Full-disk encryption and account authorization are Environment responsibilities.
- SHA-256 digests provide integrity detection, not authenticated issuer identity. Signature/trust chains remain deferred.

Prefer keeping practitioner data outside the repository, for example:

```text
Windows: %LOCALAPPDATA%\AgentSpells\
Unix:    ${XDG_DATA_HOME:-~/.local/share}/agent-spells/

AgentSpells/
  registry/
    books/
  familiars/
```

If repository-local storage is used for development, keep it under `.agent-spells-local/`, which is ignored by Git.

## Repository map

```text
README.md                 orientation and current practitioner path
FOUNDATIONS.md            meaning, invariants, domains, lifecycle crossings
AGENT_SPELLS.md           earlier structural baseline and validation history
AGENTS.md                  repository participation rules for agents
CLAUDE.md                  Claude-oriented adaptation of AGENTS.md
REPOSITORY_AUDIT.md        file-by-file purpose and lifecycle audit
FIRST_FAMILIAR_SEAL.md     previous frozen first-cast seal
MIDNIGHT_FIRST_FAMILIAR.md corrected Owl-led midnight candidate and procedure

spell/                     declared possibility and Spellcraft
cast/                      invariant casting runtime, practitioner loop, tests, examples
familiar/                  Familiar contract, Owl, Find Familiar, validation, persistence
registry/                  Scroll / Spellbook / Library / local registration
environment/               host mechanisms such as Presence
```

Detailed file purposes live in [REPOSITORY_AUDIT.md](REPOSITORY_AUDIT.md). The previous seal remains historical evidence; it is not silently rewritten.

## Status

The current midnight candidate proves or retains:

- exact Spell name/version/digest registration and resolution;
- local Spellbook persistence across restart;
- Familiar validation owned by the Familiar domain;
- exact Familiar persistence across restart;
- tamper detection for local Spellbook and Familiar storage;
- explicit subject acceptance before Find Familiar persistence;
- `owl.agent` occupying the caster role while `bdo` remains the subject of the first Find Familiar proof;
- `owl.system` participating as Owl's Familiar in that proof;
- refusal before effectful persistence when the subject has not accepted the candidate;
- bounded session Presence and Summon Familiar mechanics;
- CI execution of the complete `cast/tests` suite.

Explicitly deferred:

- generic Binding-backed Practitioner resolution and cast refusal when that relation is absent;
- renaming the historical `caster` ownership field inside the Familiar schema/store to a durable bound-subject relation;
- issuer signatures / trust chains;
- remote Library transport and polling;
- semantic-version ranges;
- Presence lifetimes beyond session;
- a Dismiss Spell;
- standing / reliability grades derived from broader CAST evidence.

No example is granted universal Spell standing merely because tests pass. Tests and CAST evidence support or defeat claims; they do not become doctrine by existing.

## Test

```bash
python -m pip install PyYAML jsonschema
PYTHONPATH=cast:environment:. python -m unittest discover -s cast/tests -v
```

On Windows PowerShell:

```powershell
python -m pip install PyYAML jsonschema
$env:PYTHONPATH = "cast;environment;."
python -m unittest discover -s cast/tests -v
```

## Source baselines

Reviewed 2026-08-15:

- Agent Skills specification
- MCP specification revision 2026-07-28
- MCP 2026-07-28 release notes

Agent Spells is an independent experimental protocol and is not part of Agent Skills or MCP.
