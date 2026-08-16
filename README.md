# Agent Spells

Agent Spells is an experimental local-first protocol for declaring **Spells**, attempting their **Effects** through one invariant casting law, preserving exact runtime evidence as **CAST** records, and keeping caster-owned guidance in **Familiars** without confusing guidance with authority.

The repository is organized around five subject domains:

- **Spell** — portable Effect declarations, Requirements, Telemetry, and Spellcraft.
- **Cast** — situated invocation, closure, governed execution, observation, residuals, and CAST records.
- **Familiar** — caster-owned dialect, attention, preferences, stake, advisory authority, validation, and persistence.
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

## Current practitioner path

The first practitioner-facing path is intentionally small:

```text
Summon owl.system
    -> Owl is Present for the session

Cast find-familiar@0.1.0
    -> prepare complete Familiar candidates
    -> practitioner Marks / corrections
    -> practitioner explicitly accepts one complete candidate
    -> closure
    -> persist the exact accepted Familiar
    -> return FamiliarRef

Resolve FamiliarRef after restart
    -> exact accepted Familiar is recovered

Optional later:
Cast summon-familiar@0.1.0(target = FamiliarRef)
    -> caster Familiar becomes Present for the session
```

`caster-accepted` is a **before Requirement** for Find Familiar: persistence may not begin until the caster has accepted the complete candidate.

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
FIRST_FAMILIAR_SEAL.md     frozen first-cast readiness statement and procedure

spell/                     declared possibility and Spellcraft
cast/                      invariant casting runtime, practitioner loop, tests, examples
familiar/                  Familiar contract, Owl, Find Familiar, validation, persistence
registry/                  Scroll / Spellbook / Library / local registration
 environment/              host mechanisms such as Presence
```

Detailed file purposes live in [REPOSITORY_AUDIT.md](REPOSITORY_AUDIT.md).

## Status

The current first-cast candidate proves:

- exact Spell name/version/digest registration and resolution;
- local Spellbook persistence across restart;
- Familiar validation owned by the Familiar domain;
- exact Familiar persistence across restart;
- tamper detection for local Spellbook and Familiar storage;
- practitioner preparation + explicit acceptance before closure;
- `find-familiar@0.1.0` through the current Technique Binding + invariant cast path;
- refusal before effectful persistence when the candidate has not been accepted;
- bounded session Presence and Summon Familiar mechanics;
- CI execution of the complete `cast/tests` suite.

Explicitly deferred and not required for a local first Find Familiar cast:

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
