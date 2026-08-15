# Canonical Spell Form v0

A Spell SHOULD be authored and presented through six named typed parts:

> **Domain · Cost · Instructions · Power · Components · Effects**

These are the human-facing anatomy of a Spell. The Spell Runtime compiles and evaluates runtime concerns such as telemetry, requirements, limits, evidence, Trials, Level, Grade, and receipts over this form.

Telemetry is deliberately not a seventh authored part. Telemetry is the observed state used to prove the current condition of the Spell's parts during a concrete cast.

## 1. Domain

**Magic meaning:** what kind of magic this is and where it belongs.

**Operational meaning:** the versioned measurement, vocabulary, authority, and conformance profile under which the Spell's claims are meaningful.

A Domain entry is typed by:

```yaml
domain:
  id: software.repository
  version: 0.1
  scope: local-workspace
  target_types: [repository, file]
```

A Spell MAY support several domains, but Level and Grade MUST remain domain-qualified.

Domain determines or references:

- native scalar definitions
- normalization rules
- scope-envelope vocabulary
- authority/consequence vocabulary
- required Trial families
- Level-shell requirements

## 2. Cost

**Magic meaning:** what casting consumes or puts at stake.

**Operational meaning:** resources that must be available, committed, reserved, or risked for a cast.

Cost is typed. A Spell MUST NOT collapse unlike costs into fictional mana unless its domain genuinely defines such a scalar.

Recommended cost types:

- `attention`
- `time`
- `compute`
- `memory`
- `storage`
- `network`
- `money`
- `tool-use`
- `user-effort`
- `authority`
- `risk`
- `material`
- `evidence`
- domain-defined cost type

Example:

```yaml
cost:
  - type: time
    estimate: 30
    unit: s
  - type: compute
    bound: low
  - type: authority
    requires: workspace-write
```

Cost SHOULD distinguish:

- `required` — must be available for the cast
- `committed` — actually spent/allocated
- `maximum` — hard limit
- `observed` — measured after or during the cast

## 3. Instructions

**Magic meaning:** how the Spell is cast.

**Operational meaning:** the portable procedure, invocation semantics, and decision rules that turn intent plus current state into an effect.

Instructions MAY contain:

- magic words / incantations
- natural-language invocation patterns
- expressions
- ordered procedure
- branching rules
- blocking/reduction rules
- recovery behavior
- verification procedure

Instructions are NOT allowed to waive Domain, Cost, Power, Component, authority, telemetry, or effect-evidence constraints.

Example:

```yaml
instructions:
  magic_words: ["Prestidigitation"]
  expression: tidy
  procedure:
    - observe target state
    - determine smallest valid transformation
    - preview when ambiguity is material
    - apply within power and cost envelope
    - verify the resulting effect
```

A migrated Agent Skill may preserve `SKILL.md` as all or part of its Instructions implementation.

## 4. Power

**Magic meaning:** how much effect the Spell can govern.

**Operational meaning:** the demonstrated scope envelope within a Domain, plus any cast-specific requested or permitted envelope.

Power is NOT Level alone.

Power is expressed first in native scope terms:

```yaml
power:
  domain: software.repository@0.1
  envelope:
    target_count: {max: 20}
    environments: {max: 1}
    actors: {max: 1}
    consequence: local-nonproduction
    reversibility: required
```

The runtime may normalize these measurements under the Domain profile and derive a demonstrated Level from Trials.

Power MUST distinguish where useful:

- `requested` — what the caster asks for now
- `available` — what current telemetry and authority permit
- `demonstrated` — what Trials have previously proven
- `used` — the actual effect envelope of this cast

A cast MUST NOT silently exceed the intersection of requested, available, demonstrated, and allowed Power.

## 5. Components

**Magic meaning:** what must participate in the Spell.

**Operational meaning:** typed participants, capabilities, resources, materials, observations, or persistent foci required or optionally used by the cast.

A Component has a stable type plus a role in the Spell.

Core component types:

- `caster` — actor directing/authorizing the cast
- `familiar` — persistent expressive casting mediator
- `focus` — persistent object/state used to stabilize or address casting
- `tool` — callable capability used to observe or enact
- `material` — artifact/data/resource consumed or transformed
- `target` — object/system the effect applies to
- `environment` — runtime/place in which observation or effect occurs
- `telemetry-source` — capability that can provide required current observations
- `authority` — credential/approval/capability boundary authorizing action
- `reference` — non-consumed example, pattern, specification, or bearing
- `catalyst` — one-time input that initiates or materially enables an expression
- domain-defined component type

Example:

```yaml
components:
  - type: caster
    required: true
  - type: familiar
    required: false
  - type: target
    role: workspace
    required: true
  - type: tool
    role: filesystem
    capability: read-write
  - type: focus
    role: reversible-baseline
    accepts: git-checkpoint
  - type: telemetry-source
    role: workspace-state
```

Component requirements are declarative. At cast time telemetry proves whether the required components actually exist, are fresh enough, possess the required capability, and remain within authority.

## 6. Effects

**Magic meaning:** what changes when the Spell resolves.

**Operational meaning:** the permitted effect classes, expected consequence, actual observed result, evidence requirements, and residuals.

Effects SHOULD distinguish:

- `possible` — effect classes inherent to the Spell
- `expected` — intended effect for this cast
- `actual` — what occurred
- `evidence` — observations/artifacts proving the actual effect
- `residuals` — intended portions not achieved
- `recovery` — effect needed to restore or contain failed/partial casting where applicable

Example:

```yaml
effects:
  possible: [normalize, rename, annotate]
  expected:
    type: normalize
    target: selected-generated-files
  evidence:
    - before-after-manifest
    - diff
```

A described effect without sufficient evidence does not increase demonstrated Spell standing.

# Runtime compilation

The six authored parts compile into runtime governance approximately as follows:

```text
DOMAIN
  -> scalar vocabulary
  -> normalization
  -> authority/consequence semantics
  -> Trial + Level rules

COST
  -> energy requirements
  -> resource ceilings
  -> observed expenditure

INSTRUCTIONS
  -> invocation
  -> expressions
  -> casting procedure
  -> branching/blocking/recovery logic

POWER
  -> requested/available/demonstrated/used scope envelopes
  -> limits
  -> Level evidence

COMPONENTS
  -> dependencies
  -> capabilities
  -> telemetry requirements
  -> authority/material/focus resolution

EFFECTS
  -> expected effect
  -> actual effect
  -> evidence
  -> residuals
  -> recovery
```

`requirements` and `limits` are therefore runtime predicates over the Spell Form rather than necessarily separate human-facing sections.

Examples:

```text
Requirement:
  required component `workspace` is present and observable

Limit:
  used Power must remain <= available Power

Requirement:
  required Cost `workspace-write authority` is available

Limit:
  committed compute must remain <= Cost.maximum

Requirement:
  actual Effect must have required evidence before status=resolved
```

# Typed components vs six parts

The six Spell parts are not themselves Components.

`Components` is one of the six parts and contains the named typed things that participate in casting.

This distinction keeps the grammar small:

```text
SPELL
├── Domain
├── Cost
├── Instructions
├── Power
├── Components
│   ├── Caster
│   ├── Familiar
│   ├── Focus
│   ├── Tool
│   ├── Material
│   ├── Target
│   ├── Environment
│   ├── Telemetry Source
│   ├── Authority
│   ├── Reference
│   └── Catalyst
└── Effects
```

# Skill -> Trick -> Spell mapping

The canonical form makes migration legible.

A Skill often already supplies:

- `Instructions`
- some `Components` such as scripts/references/tools
- an intended `Effect`

A Trick adds a bounded, evidenced Effect and a recognizable invocation/expression.

A Level 0 Spell additionally demonstrates:

- a Domain with meaningful current-state distinctions
- Cost that is observed/bounded where relevant
- Power whose scope is actually enforced
- Components whose presence/capabilities are resolved from reality
- Instructions that change behavior when relevant conditions change
- Effects that are evidenced

This is the upgrade rather than a rewrite.

# Example: Prestidigitation / tidy

```yaml
spell: Prestidigitation

domain:
  id: workspace.transformation
  version: 0.1
  scope: local

cost:
  - type: attention
    requested: light
  - type: compute
    maximum: bounded-local
  - type: authority
    requires: workspace-write

instructions:
  magic_words: ["Prestidigitation"]
  expression: tidy
  procedure:
    - inspect
    - choose-smallest-valid-transformation
    - preview-if-ambiguous
    - apply
    - verify

power:
  envelope:
    target_count: {max: 20}
    environments: {max: 1}
    consequence: local
    reversibility: required

components:
  - {type: caster, required: true}
  - {type: target, role: workspace, required: true}
  - {type: tool, role: filesystem, required: true}
  - {type: focus, role: reversible-baseline, required: true}
  - {type: telemetry-source, role: workspace-state, required: true}

effects:
  possible: [normalize, rename, remove-proven-generated-artifact]
  evidence: [before-after-manifest, diff]
```

# Example: Familiar / summon

```yaml
spell: Familiar

domain:
  id: identity.familiar
  version: 0.1

cost:
  - type: user-effort
    role: recognition-and-correction
  - type: history
    role: authorized-evidence
  - type: attention
    requested: interactive

instructions:
  magic_words: ["Summon Familiar"]
  expression: summon
  procedure:
    - gather-authorized-evidence
    - distinguish evidence-from-inference
    - summon-owl-as-guide
    - draw-candidate-form
    - collect-holder-marks
    - redraw-until-recognized-or-rejected
    - register-only-after-recognition

power:
  envelope:
    holders: {max: 1}
    candidate_form_change: allowed-before-adoption
    adopted_form_change: holder-authorized-only

components:
  - {type: caster, required: true}
  - {type: familiar, role: owl-guide, required: true}
  - {type: material, role: authorized-history, required: false}
  - {type: reference, role: preferences-and-pattern-commons, required: false}
  - {type: focus, role: familiar-registry, required: true}
  - {type: telemetry-source, role: current-runtime-and-holder-state, required: true}

effects:
  possible: [candidate-familiar, registered-familiar]
  evidence:
    - holder-recognition
    - persisted-registry-record
```

# Invariant

**A Spell should be readable as magic and auditable as a system.**

Domain says where its claims mean something. Cost says what it consumes or risks. Instructions say how it is cast. Power says how much governed effect it can support. Components say what must participate. Effects say what actually changes.
