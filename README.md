# Agent Spells

Agent Spells is an experimental local-first protocol for declaring **Spells**, attempting their **Effects** through one invariant casting law, preserving exact runtime evidence as **CAST** records, and keeping Familiar guidance distinct from runtime authority.

The repository is organized around five subject domains:

- **Spell** — portable Effect declarations, Requirements, Telemetry, and Spellcraft.
- **Cast** — situated invocation, closure, governed execution, observation, residuals, and CAST records.
- **Familiar** — dialect, attention, preferences, stake, advisory authority, validation, views, and persistence.
- **Registry** — Scrolls, Spellbooks, Libraries, exact resolution, provenance, and local registration storage.
- **Environment** — concrete host mechanisms such as Presence, observability, authority, scope, meters, clocks, containment, and conserved Mana.

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

The intended first-user path is:

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
```

The executable proof uses `owl.agent` as the caster and `owl.system` as Owl's Familiar. The subject whose Familiar is being found is not treated as the caster merely to bootstrap the protocol.

`subject-accepted` is a **before Requirement** for Find Familiar: persistence may not begin until the subject accepts the complete candidate.

The generic relation-derived Practitioner law is still explicitly deferred; the first-cast proof does not claim that every Spell currently enforces it.

## Owl, Spellcraft, and Find Familiar

```text
Owl            = Agent conducting the bootstrap interaction
owl.system     = Owl's Familiar
Spellcraft     = Skill for understanding / inspecting / repairing Spell declarations
Find Familiar  = Spell whose first-user path establishes the accepted Familiar for the subject
Technique      = implementation used to attempt an Effect
SpellCast      = runtime that closes, executes, observes, and records the Cast
```

Spellcraft does not cast Spells. Owl can use Spellcraft while conducting Find Familiar.

## Local-first storage

A personal Spellbook does **not** need to be published.

- `registry.LocalRegistry(root)` persists existing `Spellbook` objects and re-verifies exact declarations when reopened.
- `familiar.FamiliarStore(root)` persists the current exact Familiar artifact and verifies revision + digest on resolution.
- Current `FamiliarStore` storage does not retain older immutable revisions after a newer revision is written; that active defect is tracked in [#15](https://github.com/bdf1992/familiar/issues/15).
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

Repository-local development data belongs under `.agent-spells-local/`, which is ignored by Git.

## Active non-deferred work

GitHub Issues are the backlog source of truth. Do not duplicate these as free-floating TODO prose in code or specifications.

- [#10 — Enforce Scope at the effect path, not only at preflight](https://github.com/bdf1992/familiar/issues/10)
- [#11 — Enforce Authority through attenuated execution capabilities](https://github.com/bdf1992/familiar/issues/11)
- [#12 — Prevent maintenance replay by source identity and accepted receipt](https://github.com/bdf1992/familiar/issues/12)
- [#13 — Bind Cast Requirements to exact capability receipts](https://github.com/bdf1992/familiar/issues/13)
- [#14 — Make Familiar View omission semantics mechanically complete](https://github.com/bdf1992/familiar/issues/14)
- [#15 — Retain immutable Familiar revisions addressable by FamiliarRef](https://github.com/bdf1992/familiar/issues/15)
- [#16 — Integrate conserved Mana with the invariant Cast lifecycle](https://github.com/bdf1992/familiar/issues/16)
- [#17 — Remove runtime dependence on transitional Git symlinks](https://github.com/bdf1992/familiar/issues/17)
- [#18 — Refresh repository audit and lifecycle after 0.6 and Familiar View](https://github.com/bdf1992/familiar/issues/18)

Normative invariants remain in domain documents. Executable defect specimens remain in tests. The issue owns the repair specification, acceptance criteria, and implementation backlog.

## Explicitly deferred

These are outside the current active backlog above:

- generic Binding-backed Practitioner resolution and cast refusal when that relation is absent;
- renaming the historical `caster` ownership field inside the Familiar schema/store to a durable bound-subject relation;
- issuer signatures / trust chains;
- remote Library transport and polling;
- semantic-version ranges;
- Presence lifetimes beyond session;
- a Dismiss Spell;
- standing / reliability grades derived from broader CAST evidence;
- Level 0 Spell semantics and portable Mana/level fields;
- wall-clock drain scheduling;
- external signatures/seals for the Mana ledger;
- multi-host consensus/concurrent mutation.

## Repository map

```text
README.md                 orientation, current status, issue/defer boundary
FOUNDATIONS.md            meaning, invariants, domains, lifecycle crossings
AGENT_SPELLS.md           earlier structural baseline and validation history
AGENTS.md                  repository participation rules for agents
CLAUDE.md                  Claude-oriented adaptation of AGENTS.md
REPOSITORY_AUDIT.md        lifecycle audit; refresh tracked by issue #18
FIRST_FAMILIAR_SEAL.md     previous frozen first-cast seal
MIDNIGHT_FIRST_FAMILIAR.md corrected Owl-led first-cast candidate and procedure

spell/                     declared possibility and Spellcraft
cast/                      invariant casting runtime, practitioner loop, tests, examples
familiar/                  Familiar contract, Owl, guidance, view/report work, persistence
registry/                  Scroll / Spellbook / Library / local registration
environment/               Presence and conserved Magic runtime mechanisms
```

The historical seals remain evidence of prior crossings; they are not silently rewritten.

## Status and evidence

Current `main` retains successful CI coverage of the complete `cast/tests` suite, including the 0.6 Magic runtime. Passing tests are mechanics evidence, not universal Spell standing.

The Scope containment defect remains an executable expected-failure specimen until #10 closes; it is not considered resolved merely because the rest of CI is green.

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

Windows checkout portability is tracked by #17 until the runtime no longer depends on transitional symlink behavior and CI proves the documented path.

## Source baselines

Reviewed 2026-08-15:

- Agent Skills specification
- MCP specification revision 2026-07-28
- MCP 2026-07-28 release notes

Agent Spells is an independent experimental protocol and is not part of Agent Skills or MCP.
