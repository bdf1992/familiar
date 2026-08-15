# Spell Protocol v0

A Spell is a telemetry-aware, contract-governed expressive capability. It is inspired by the portability and progressive disclosure of Agent Skills and the typed capability surfaces of MCP, but it adds runtime requirements for live state, limits, energy, evidence, trials, grading, and cast receipts.

## Core invariant

A Spell is not valid because its package parses. A Spell earns standing through demonstrated behavior.

Three questions are always distinct:

1. **Definition validity** — is this a coherent Spell definition?
2. **Cast validity** — can this Spell be cast here, now, by this caster, under current telemetry and limits?
3. **Effect validity** — did the claimed effect actually occur, and is there evidence appropriate to the consequence?

## Dual vocabulary

Every magic term MUST have an operational definition.

| Magic word | Operational meaning |
|---|---|
| Spell | telemetry-aware, contract-governed expressive capability |
| Cast | one runtime application of a Spell to a concrete situation |
| Caster | actor directing or authorizing the cast |
| Familiar | persistent mediator of caster expression, preferences, history, and systemic pull |
| Summon | resolve/load a persistent participant into casting context |
| Magic words | compact human-facing invocation |
| Energy | resources available or committed to a cast |
| Telemetry | observed current state required to ground the cast |
| Requirement | condition that must hold for the cast to proceed or resolve |
| Limit | boundary the cast may not cross |
| Expression | one realization of the Spell's inherent ability |
| Effect | actual consequence produced by the cast |
| Evidence | proof appropriate to the claimed effect |
| Residual | unresolved portion of the intended effect |
| Trick | bounded recognizable effect without demonstrated Spell governance |
| Level | demonstrated breadth/depth of governed casting space |
| Grade | quality/reliability within demonstrated casting space |
| Mastery | caster/Familiar ability to use a Spell effectively |
| Trial | scenario used to demonstrate Spell behavior under changed conditions |
| Spellbook | installed/discoverable Spell definitions and demonstrated standings |

If a magic term cannot be explained operationally without using other magic terms, the definition is incomplete.

## Definition contract

A portable Spell definition MUST declare:

- `identity`
  - stable `id`
  - semantic `version`
  - human-readable `name`
  - one `inherent_ability`
- `invocation`
  - zero or more `magic_words`
  - one or more known `expressions`
- `telemetry`
  - required observations
  - optional observations
  - any coverage/freshness constraints
- `requirements`
  - preconditions or invariants that must hold
- `limits`
  - authority, scope, resource, consequence, reversibility, or other hard boundaries
- `energy`
  - resources the Spell understands and any bounds relevant to casting
- `effect`
  - schema or description of the effect class the Spell may produce
- `evidence`
  - evidence required to support claimed effects
- `evaluation`
  - declared trials
  - optional claimed level

A Spell MAY package human-facing instructions, scripts, references, assets, icons, examples, MCP configuration, or adapters. Those are implementation resources, not substitutes for the contract.

## Input, telemetry, inference, assumption

The runtime MUST preserve these distinctions:

- **Input** — intentionally supplied by the caster or caller.
- **Telemetry** — observed state with provenance.
- **Inference** — value derived from inputs and/or telemetry.
- **Assumption** — unresolved proposition temporarily treated as true.

A Spell MUST NOT upgrade an assumption into telemetry merely because the assumption is plausible.

Telemetry SHOULD record source, observed time, scope/coverage, and freshness when material to validity.

## Requirements and limits

Requirements and limits are not interchangeable.

- Missing **requirement**: the cast is `blocked`, or the runtime may reduce the cast if the Spell defines a valid reduced expression.
- Exceeded **limit**: the cast MUST NOT proceed across that boundary. The runtime may refuse or reduce the cast.
- Uncertain requirement: the runtime may probe for telemetry before deciding.

Correct blocking is evidence of Spell quality, not failure.

## Energy

Energy is an open resource ledger, not a required scalar or fictional mana value.

Examples include:

- attention
- user effort
- time
- context
- compute
- tools
- materials
- authority
- history
- evidence budget
- monetary or environmental budget when relevant

Each Spell declares only the resources that materially affect its casting.

Higher committed energy MAY increase scope, fidelity, search depth, verification, or duration. It MUST NOT erase Spell identity, requirements, limits, or authority boundaries.

## Cast lifecycle

The reference lifecycle is intentionally small:

`invoked -> ready | blocked -> casting -> resolved | failed`

The runtime MAY expose additional events, but portable behavior SHOULD NOT depend on a richer lifecycle.

A runtime cast records at least:

- Spell identity/version
- caster
- participating Familiar(s), if any
- target/context
- resolved intent/expression
- telemetry actually used
- requirements satisfied or missing
- limits resolved/applied
- energy available/committed
- expected effect
- actual effect
- evidence
- residuals
- status

## Effect receipts

A resolved cast MUST produce a receipt sufficient to inspect the claimed effect.

A receipt SHOULD contain:

- cast identifier
- Spell identifier/version
- target
- intent/expression
- material telemetry references
- requirements and limits applied
- energy committed where consequential
- effect summary and artifact references
- evidence references
- residuals
- final status

The receipt is not hidden reasoning and MUST NOT contain secrets or private chain-of-thought.

## Tricks, levels, grades, and mastery

Spellcraft is graded, not binary.

### Trick standing

A Trick is a bounded technique or effect that has not demonstrated enough runtime governance to qualify as a Level 0 Spell.

Suggested standings:

- `novice-trick`
- `practiced-trick`
- `master-trick`

A Master Trick can be excellent and SHOULD NOT be pressured into becoming a Spell if telemetry-sensitive governance would add no value.

### Level

Level measures demonstrated casting range, not quality or prestige.

- `0` is the minimum demonstrated Spell: relevant telemetry changes valid casting; requirements/limits are enforced; a bounded effect can be evidenced.
- `1-3` demonstrate broader expressions, meaningful energy scaling, stronger degradation behavior, or wider telemetry-sensitive range.
- `4-6` demonstrate substantial adaptive range, multi-mode or multi-environment operation where inherent to the Spell, and stronger interactions among telemetry, state, limits, and energy.
- `7-9` demonstrate high-order, consequential, long-horizon, or cross-system governance with strong evidence and failure discipline.

These bands are protocol guidance, not a substitute for concrete trials.

### Grade

Grade measures how well the implementation governs its demonstrated range. Runtimes MAY use numeric or letter grades, but MUST publish the rubric used.

### Mastery

Mastery belongs to a caster/Familiar/Spell relationship. It MUST NOT be confused with Spell level or implementation grade.

## Trials

Spells are demonstrated through Trials.

A Trial changes relevant conditions and asks whether casting behavior changes correctly. Useful variations include:

- telemetry present vs absent
- fresh vs stale telemetry
- authorized vs unauthorized target
- small vs large scope
- low vs high energy
- reversible vs irreversible environment
- normal vs degraded capability surface
- successful effect vs partial effect vs failed effect

A core diagnostic rule:

> If changing telemetry declared as relevant never changes the valid casting space, that telemetry claim is probably decorative.

Trial evidence determines demonstrated standing independently of claimed level.

## Skill -> Trick -> Spell migration

Existing Skills are first-class migration sources.

A migration SHOULD preserve the existing Skill package and competence. The minimum progression is:

1. **Skill** — keep `SKILL.md`, scripts, references, assets, examples, and learned procedures.
2. **Trick** — identify one bounded recognizable effect and expose it as an expression with explicit evidence.
3. **Level 0 candidate** — add Spell contract fields for telemetry, requirements, limits, energy, and effect evidence.
4. **Trial** — demonstrate that relevant telemetry changes behavior, that boundaries are enforced, and that claimed effects are evidenced.
5. **Spell** — runtime records demonstrated level/grade; the original Skill remains usable as implementation material.

A migration MUST NOT require rewriting a working Skill into fantasy vocabulary. Magic words are a human-facing interface; operational definitions remain authoritative.

## MCP composition

MCP is a capability/transport substrate, not the Spell definition.

A Spell runtime MAY use MCP to:

- discover tools
- obtain structured schemas
- invoke effects
- read resources
- gather telemetry
- obtain user elicitation where appropriate
- use explicit state handles
- negotiate supported extensions

Spell SHOULD reuse MCP authorization and transport where applicable rather than defining competing transport semantics.

MCP tools MAY advertise Spell-related annotations or extension metadata in the future, but a tool does not become a Spell merely by exposing a tool schema.

## Familiar and Owl

`Familiar` is the first native Spell targeted by this protocol.

Its intended ability is to form and maintain a recognizable expressive mediator between a caster and their use of Spells.

The **Owl** is the system Familiar specializing in forming Familiars, continuity, completion, and Spellcraft guidance. Owl advice cannot manufacture telemetry, authority, or evidence.

The Familiar's form may develop but MUST NOT autonomously replace itself after holder adoption. Form replacement requires holder-authorized identity change or reassignment.

## Protocol design rule

Spell MUST remain compatible with two unlike native examples:

- Familiar: persistent, identity-bearing, historical, expressive.
- Prestidigitation: lightweight, bounded, flexible, frequently ephemeral.

If a protocol rule exists only because Familiar needs it, it belongs in Familiar unless Prestidigitation or another independent Spell demonstrates the same invariant.
