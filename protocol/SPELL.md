# Spell Protocol v0

A Spell is a telemetry-aware, contract-governed expressive capability. It is inspired by the portability and progressive disclosure of Agent Skills and the typed capability surfaces of MCP, but it adds runtime requirements for live state, limits, energy, evidence, trials, grading, cast receipts, and explicit handling of unexpected effects.

## Core invariant

A Spell is not valid because its package parses or its author calls it magic. A Spell earns standing through demonstrated runtime behavior.

Three questions are always distinct:

1. **Definition validity** — is this a coherent castable Spell candidate?
2. **Cast validity** — can it be cast here, now, by this caster, under current telemetry, requirements, limits, and available energy?
3. **Effect validity** — what actually happened, what evidence supports it, and what remains unresolved or unexpected?

Spellcraft may create a valid Spell candidate. Runtime evidence determines whether that candidate is a Trick or demonstrated Spell.

## Dual vocabulary

Every magic term MUST have an operational definition.

| Magic word | Operational meaning |
|---|---|
| Spell | telemetry-aware, contract-governed expressive capability |
| Spellcraft | Skill for studying, designing, testing, migrating, and repairing Spell candidates |
| Cast | one runtime application of a Spell to a concrete situation |
| Casting | runtime-governed execution of one cast |
| Caster | actor directing or authorizing the cast |
| Familiar | persistent structured mediator of caster expression, preferences, history, stake, and systemic pull |
| Summon | resolve/load a persistent participant into casting context |
| Magic words | compact human-facing invocation; never mandatory syntax |
| Energy | resources available or committed to a cast |
| Telemetry | observed current state required to ground the cast |
| Requirement | condition that must hold for the cast to proceed or resolve |
| Limit | boundary the cast may not cross |
| Expression | one realization of the Spell's inherent ability |
| Technique | known implementation or procedure for realizing an Expression |
| Effect | actual consequence produced by the cast |
| Evidence | proof appropriate to the claimed effect |
| Residual | intended effect left unresolved, unverified, or intentionally untouched |
| Fizzle | cast unable to validly resolve its intended effect |
| Disturbance | unexpected environmental observation with unresolved causality |
| Wild magic | materially unexpected cast-related effect outside the expected effect model |
| Trick | bounded recognizable effect without demonstrated Spell governance |
| Level | demonstrated breadth/depth of governed casting space |
| Grade | quality/reliability within demonstrated casting space |
| Mastery | caster/Familiar ability to use a Spell effectively |
| Trial | scenario used to demonstrate Spell behavior under changed conditions |
| Spellbook | installed/discoverable Spell definitions and demonstrated standings |

If a magic term cannot be explained operationally without using other magic terms, the definition is incomplete.

## Definition contract

A portable Spell candidate MUST declare:

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
- `unexpected`
  - how the cast records and responds to fizzles, disturbances, wild magic, and residuals
- `evaluation`
  - declared Trials
  - optional target or claimed level, never authoritative standing

A Spell MAY package human-facing instructions, Skills, Techniques, scripts, references, assets, icons, examples, MCP configuration, or adapters. Those are implementation resources, not substitutes for the contract.

## Spellcraft boundary

Spellcraft is a Skill, not a Spell and not a casting runtime.

Spellcraft MAY:

- study an inherent ability;
- migrate Skills and Tricks into Spell candidates;
- define telemetry, requirements, limits, energy, Expressions, Techniques, evidence, and Trials;
- use libraries, tools, existing Skills, cast receipts, other casters, or environmental investigation;
- optionally invoke a Familiar or other Spell as a separate cast when a runtime is available.

Spellcraft MUST NOT:

- fabricate runtime telemetry;
- declare an effect successful without evidence;
- assign demonstrated Spell standing from design intent;
- require a Familiar or Spell Runtime merely to craft a candidate.

A Spell candidate is an artifact of Spellcraft. A demonstrated Spell is a runtime classification.

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

- Missing **requirement**: the cast is blocked/fizzled before effect, or the runtime may reduce the cast if the Spell defines a valid reduced Expression.
- Exceeded **limit**: the cast MUST NOT proceed across that boundary. The runtime may refuse or reduce the cast.
- Uncertain requirement: the runtime may probe for telemetry before deciding.

Correct blocking is evidence of Spell quality, not failure of Spellhood.

## Energy

Energy is an open resource ledger, not a required scalar or fictional mana value.

Examples include attention, user effort, time, context, compute, tools, materials, authority, history, evidence budget, money, or environmental budget when relevant.

Each Spell declares only resources that materially affect casting.

Higher committed energy MAY increase scope, fidelity, search depth, verification, duration, or number of Expressions considered. It MUST NOT erase Spell identity, requirements, limits, or authority boundaries.

## Familiar interoperability

Every demonstrated Spell MUST be compatible with any protocol-valid structured Familiar as an optional casting advisor unless the Spell explicitly forbids all Familiar participation for a justified domain reason.

A Familiar MAY:

- interpret caster preferences and stake;
- suggest an Expression or Technique;
- recommend proportionate energy;
- notice risks, shadows, or residuals;
- help communicate the cast to the caster.

A Familiar MUST NOT:

- manufacture telemetry;
- widen authority;
- waive Spell requirements or limits;
- change the Spell's inherent ability;
- claim runtime evidence that was not observed;
- autonomously replace its adopted form.

The Spell MUST NOT require knowledge of a Familiar's particular icon, creature, metaphor, language, or ontology. A Stag, Owl, Lighthouse, Tree, or valid user-authored Familiar must be able to assist through the same structured participation surface.

Malformed Familiars MUST be rejectable without corrupting the cast.

At least one **foreign Familiar Trial** SHOULD be required for Level 0 standing: a valid Familiar other than the one used while crafting the candidate must participate without violating the invariants above.

## Cast lifecycle

The portable lifecycle remains intentionally small:

`invoked -> ready | blocked -> casting -> resolved | partial | fizzled`

The runtime MAY expose additional events, but portable behavior SHOULD NOT depend on a richer lifecycle.

A runtime cast records at least:

- Spell identity/version;
- caster;
- participating Familiar(s), if any;
- target/context;
- resolved intent/Expression;
- telemetry actually used;
- requirements satisfied or missing;
- limits resolved/applied;
- energy available/committed;
- expected effect;
- actual impact/effect;
- evidence;
- residuals;
- disturbances;
- suspected or confirmed wild magic;
- resolution status.

## Fizzle, disturbance, wild magic, and residuals

These are separate observations and MUST NOT be collapsed into one success/failure flag.

### Fizzle

A cast **fizzles** when it cannot validly resolve its intended effect because a required part of the cast is absent, invalid, incompatible, or breaks during execution.

Examples include invalid Spell definition, missing authority, required telemetry loss, unresolvable target, unenforceable hard limit, or failure of a required Technique.

A fizzle does **not** prove that nothing happened.

### Residual

A **residual** is an intended portion of the effect that remains unresolved, unverified, blocked, or deliberately untouched.

Residual awareness is positive evidence of Spell quality when it accurately bounds what the cast did not accomplish.

### Disturbance

A **disturbance** is an unexpected environmental observation whose relation to the cast is not yet established.

The runtime MUST NOT automatically attribute a disturbance to the Spell. Investigation may classify it as unrelated, expected-but-undocumented, implementation defect, or wild magic.

### Wild magic

**Wild magic** is a materially unexpected effect attributable or strongly linked to the cast and outside its expected effect model.

Wild magic may be beneficial, neutral, harmful, or merely strange. The runtime MUST preserve it as evidence rather than silently redefining the expected effect after the fact.

A mature Spell is not required to prevent all surprise. It is required to notice when reality has escaped its model and respond proportionately.

## Recovery paths

When a cast fizzles or a disturbance/wild effect appears, the runtime or Owl MAY recommend one or more bounded recovery paths:

- **Spellcraft** — when the Spell candidate, its effect model, requirements, limits, or Trials appear malformed;
- **Familiar** — when caster expression, stake, interpretation, or Technique choice appears mismatched;
- **another Casting** — when the Spell is sound and a separate bounded effect remains;
- **another Caster** — when independent expertise, authority, reproduction, or perspective is needed;
- **environment investigation** — when causality is uncertain or the environment itself may be disturbed.

Do not automatically retry an unexplained fizzle or wild effect.

## Effect receipts

Every cast that begins effectful execution SHOULD produce a receipt, including fizzled or partial casts when consequences may have occurred.

A receipt SHOULD contain:

- cast identifier;
- Spell identifier/version;
- target;
- intent/Expression;
- material telemetry references;
- requirements and limits applied;
- energy committed where consequential;
- effect/impact summary and artifact references;
- evidence references;
- residuals;
- disturbances;
- wild-magic status and evidence;
- resolution status.

The receipt is not hidden reasoning and MUST NOT contain secrets or private chain-of-thought.

## Tricks, levels, grades, and mastery

Spellcraft is graded, not binary.

### Trick standing

A Trick is a bounded Technique or effect that has not demonstrated enough runtime governance to qualify as a Level 0 Spell.

Suggested standings:

- `novice-trick`
- `practiced-trick`
- `master-trick`

A Master Trick can be excellent and SHOULD NOT be pressured into becoming a Spell if telemetry-sensitive governance would add no value.

### Level

Level measures demonstrated casting range, not quality or prestige.

- `0` is the minimum demonstrated Spell: relevant telemetry changes valid casting; requirements/limits are enforced; a bounded effect can be evidenced; unexpected impacts can be represented; and a valid foreign Familiar can assist without corrupting the cast.
- `1-3` demonstrate broader Expressions, meaningful energy scaling, stronger degradation/recovery behavior, or wider telemetry-sensitive range.
- `4-6` demonstrate substantial adaptive range, multi-mode or multi-environment operation where inherent to the Spell, and stronger interactions among telemetry, state, limits, energy, Familiars, and recovery.
- `7-9` demonstrate high-order, consequential, long-horizon, or cross-system governance with strong evidence, custody, disturbance handling, and failure discipline.

These bands are protocol guidance, not a substitute for concrete Trials.

### Grade

Grade measures how well the implementation governs its demonstrated range. Runtimes MAY use numeric or letter grades, but MUST publish the rubric used.

### Mastery

Mastery belongs to a caster/Familiar/Spell relationship. It MUST NOT be confused with Spell level or implementation grade.

## Trials

Spells are demonstrated through Trials.

A Trial changes relevant conditions and asks whether casting behavior changes correctly. Useful variations include:

- telemetry present vs absent;
- fresh vs stale telemetry;
- authorized vs unauthorized target;
- small vs large scope;
- low vs high energy;
- reversible vs irreversible environment;
- normal vs degraded capability surface;
- one valid Familiar vs another valid Familiar;
- malformed Familiar;
- successful effect vs partial effect vs fizzle;
- expected effect vs environmental disturbance;
- recoverable vs unrecoverable wild magic.

Core diagnostic rules:

> If changing telemetry declared as relevant never changes the valid casting space, that telemetry claim is probably decorative.

> If changing a valid Familiar changes the Spell's inherent ability or authority instead of only its guidance/expression, Familiar interoperability is defective.

> If unexpected impact is silently rewritten as intended success, effect validity is defective.

Trial evidence determines demonstrated standing independently of claimed level.

## Skill -> Trick -> Spell migration

Existing Skills are first-class migration sources.

A migration SHOULD preserve the existing Skill package and competence. The minimum progression is:

1. **Skill** — keep `SKILL.md`, scripts, references, assets, examples, and learned procedures.
2. **Trick** — identify one bounded recognizable effect and expose it as an Expression with explicit evidence.
3. **Spell candidate** — add the Spell contract around existing competence: telemetry, requirements, limits, energy, effect/evidence, unexpected-effect handling, and Trials.
4. **Trial** — demonstrate that relevant reality changes behavior, boundaries are enforced, effects/residuals are observable, and a foreign Familiar can assist safely.
5. **Spell** — runtime records demonstrated Level/Grade; the original Skill may remain a Technique or implementation material.

A migration MUST NOT require rewriting a working Skill into fantasy vocabulary. Magic words are a human-facing interface; operational definitions remain authoritative.

## MCP composition

MCP is a capability/transport substrate, not the Spell definition.

A Spell runtime MAY use MCP to discover tools, obtain structured schemas, invoke effects, read resources, gather telemetry, obtain elicitation where appropriate, use explicit state handles, or negotiate supported extensions.

Spell SHOULD reuse MCP authorization and transport where applicable rather than defining competing transport semantics.

MCP tools MAY become Techniques, probes, telemetry providers, or effect/evidence mechanisms. A tool does not become a Spell merely by exposing a schema.

## Familiar and Owl

`Familiar` is the first native Spell targeted by this protocol.

Its intended ability is to form and maintain a recognizable expressive mediator between a caster and their use of Spells.

The **Owl** is the system Familiar specializing in forming Familiars, continuity, completion, and Spellcraft guidance. Owl advice cannot manufacture telemetry, authority, evidence, or runtime standing.

The Owl SHOULD pay special attention to malformed candidates, hidden residuals, unexplained disturbances, wild magic, and spell-shaped documentation that has not become an effect.

A Familiar's form may develop but MUST NOT autonomously replace itself after holder adoption. Form replacement requires holder-authorized identity change or reassignment.

## Protocol design rule

Spell MUST remain compatible with two unlike native examples:

- Familiar: persistent, identity-bearing, historical, expressive.
- Prestidigitation: lightweight, bounded, flexible, frequently ephemeral.

If a protocol rule exists only because Familiar needs it, it belongs in Familiar unless Prestidigitation or another independent Spell demonstrates the same invariant.
