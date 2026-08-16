# Agent Spells Format 0.3 — Draft

Status: Work + Knowledge. FORMAT 0.2 remains Current until an explicit adoption crossing.

## Purpose

`SPELL.md` declares a portable Effect contract. FORMAT 0.3 makes enough of that contract machine-readable for a host, Familiar, or planner to answer four questions before a cast:

1. What typed material may enter and leave the Effect?
2. Which typed protocol operations participate?
3. Which concrete runtime capabilities must bind each Requirement?
4. Which implementations are plausible realizations without making any implementation part of Spell semantics?

A Spell still does not contain live runtime state, capability receipts, CAST evidence, standing, or an executor.

## Portable frontmatter

```yaml
---
spell_format: "0.3"
name: find-familiar
version: "0.2.0"
description: Establish an accepted Familiar artifact for a resolved subject.

schemas:
  - id: familiar
    description: Persisted Familiar artifact.
    ref: ../../../familiar/familiar.schema.json
  - id: familiar-ref
    description: Exact reference returned by Familiar persistence.
    schema:
      type: object
      required: [id, caster_id, revision, digest]

protocols:
  - id: familiar-store
    ref: familiar.store:FamiliarStore
    version: "0.1"
    operations:
      - id: put
        input: {schema: familiar}
        result: {schema: familiar-ref}
      - id: resolve
        input: {schema: familiar-ref}
        result: {schema: familiar}

runtime:
  protocols: [familiar-store]

telemetry: []

implementations:
  - id: local-familiar-store
    kind: package
    locator: familiar.store:FamiliarStore
    effects: [establish]
    protocols: [familiar-store]
    description: Reference local implementation; not required by Spell semantics.

effects:
  - id: establish
    description: Persist the exact accepted Familiar and return an exact reference.
    telemetry: []
    interface:
      result:
        schema: familiar-ref
    requirements:
      before:
        - id: subject-resolved
          description: The subject whose Familiar is being found is explicitly resolved.
          check: subject.resolved
          binding:
            operation: observe
            capability: subject-resolution

        - id: familiar-store-supported
          description: The Environment exposes exact Familiar persistence.
          check: familiar.store.available
          binding:
            operation: put
            protocol: familiar-store
            capability: familiar-store

      during: []

      after:
        - id: familiar-valid
          description: The resulting Familiar validates against the declared contract.
          check: schema.valid
          binding:
            operation: validate
            capability: schema-validator

        - id: familiar-persisted
          description: The exact Familiar resolves from the returned FamiliarRef.
          check: familiar.store.roundtrip
          binding:
            operation: resolve
            protocol: familiar-store
            capability: familiar-store
---
```

The optional Markdown body is human guidance. It cannot satisfy a Requirement.

## Top-level contract

### Identity

`spell_format`, `name`, `version`, and `description` retain their 0.2 jobs. A host must reject unsupported format versions.

### `schemas`

`schemas` names data shapes used by Effect interfaces and protocol operations. Each declaration has an `id`, description, and exactly one of:

- `ref` — a portable locator for an external schema;
- `schema` — an embedded JSON-Schema-shaped object.

FORMAT does not require JSON Schema as the only implementation language. The declaration provides a machine-addressable shape that a validator or generator can consume.

### `protocols`

`protocols` names interaction contracts that participate in realizing Effects. A protocol declaration includes an id, locator, version, and typed `operations`.

Each operation has a stable id and may declare `input` and `result` schema references. When a Requirement binds to a protocol, its `binding.operation` must name an operation declared by that protocol.

This matters because a bare operation verb is not a protocol. `put` against an unrelated store must not satisfy `familiar-store.put` merely because both advertise a write-like action.

A protocol is not a capability receipt. It states what contract is expected; the Environment still has to expose a concrete implementation at cast time.

### `runtime`

`runtime.protocols` lists protocol ids that a conforming runtime must be able to resolve for this Spell. Missing or ambiguous resolution fails closed.

This is runtime contracting, not runtime state.

### `telemetry`

Telemetry retains the 0.2/early-0.3 meaning: named observations with optional freshness bounds.

### `implementations`

`implementations` is optional non-authoritative implementation guidance. Each suggestion may identify a Skill, MCP server, script, service, host, package, or binding and state which Effects/protocols it is intended to realize.

An implementation suggestion:

- helps Familiars and hosts discover likely realizations;
- may be generated, ranked, replaced, or ignored;
- does not grant authority;
- does not prove compatibility;
- does not satisfy a Requirement merely by being listed.

### `effects`

An Effect contains telemetry references, an optional typed interface, and phase-specific Requirements.

## Typed Effect interfaces

`interface.input`, `interface.target`, and `interface.result` may reference ids declared in `schemas`.

This gives generators and Familiars a concrete contract for proposing inputs, resolving targets, validating results, and producing forms or models without pretending that generated data is runtime evidence.

## Requirements and bindings

Every Requirement has a stable id and a concrete `binding` selector. Ordinary before/after Requirements additionally carry a machine-readable `check` id.

A binding selector contains:

- required `operation`;
- and at least one of `capability`, `protocol`, or `locator`;
- optional `environment`, `subject`, and `authority` constraints when exact selection requires them.

If `protocol` is present, `operation` must resolve to an operation declared by that protocol. If more than one runtime receipt satisfies a selector and the selector cannot choose deterministically, closure must refuse as ambiguous.

CAST should retain the exact receipt/mechanism selected for every Requirement.

### Before

Before Requirements gate closure.

**Ordinary check**

```yaml
- id: target-observable
  description: The target can be observed.
  check: target.observable
  binding:
    operation: observe
    capability: target-observer
```

**Authority**

```yaml
- id: write-authority
  authority: workspace.write
  binding:
    operation: authorize
    capability: workspace-authority
    authority: workspace.write
```

**Scope**

```yaml
- id: bounded-scope
  scope:
    max_items: 2
    enforcement: effect_path
  binding:
    operation: constrain
    capability: workspace-scope
```

`enforcement: effect_path` is required in 0.3. Preflight counting alone does not enforce Scope. The Technique must receive an attenuated capability, namespace, token, handle, or equivalent Environment-owned boundary that cannot perform the forbidden out-of-scope consequence.

### During

During Requirements are governed while effectful execution occurs.

**Cost**

```yaml
- id: tool-budget
  cost:
    resource: tool_calls
    max: 1
  binding:
    operation: meter
    capability: tool-call-meter
```

**Duration**

```yaml
- id: execution-time
  duration:
    execution_max_ms: 50
  binding:
    operation: contain
    capability: execution-container
```

A declaration is insufficient unless the selected runtime mechanism participates in the actual effect path.

### After

After Requirements independently determine whether the Effect may count as resolved.

```yaml
- id: effect-confirmed
  description: The declared result is observable.
  check: effect.confirmed
  binding:
    operation: observe
    capability: result-observer
```

Executor success cannot substitute for after-Requirement evidence.

## Pydantic and generative validation

`models.py` is the reference typed model for this draft. It performs semantic validation that plain JSON Schema cannot conveniently express and generates `spell.schema.json`.

The normative rule is **model/schema equivalence**, not Pydantic dependence. Other implementations may validate the same contract in another language.

The reference model validates at least:

- unique schema, protocol, protocol-operation, telemetry, Effect, and per-Effect Requirement ids;
- all Effect telemetry references resolve;
- all Effect and protocol-operation schema references resolve;
- all runtime/Requirement/implementation protocol references resolve;
- protocol-bound Requirement operations are declared by the referenced protocol;
- implementation Effect references resolve;
- binding selectors identify more than an operation verb;
- no duplicate Cost resource per Effect;
- at most one Scope and one execution Duration Requirement per Effect;
- Scope requires effect-path enforcement;
- phase-specific Requirement forms remain phase-correct.

Because the typed model can emit JSON Schema, downstream tools may generate editors, forms, model prompts, typed SDKs, or validation fixtures from the same contract rather than maintaining parallel hand-authored shapes.

## Relationship to protocol shapes

FORMAT 0.3 does not define one universal protocol ontology. It supplies three compositional hooks:

1. `schemas` for reusable data shape;
2. typed protocol `operations` for interaction shape;
3. Requirement `binding` selectors for exact situated capability resolution.

The chain is therefore explicit:

```text
Schema -> Protocol Operation -> Requirement Binding -> Capability Receipt -> CAST Evidence
```

No link is allowed to stand in for the next one. This preserves the distinction between declared shape, declared protocol, concrete Environment capability, and situated evidence.

## Familiar-facing minimum

The format now supports near-term Familiar work without giving Familiar semantic authority. A Familiar can:

- inspect typed Effect and protocol input/result shapes;
- inspect required protocols and runtime capabilities before proposing a cast;
- rank or suggest implementations;
- generate candidate data against declared schemas;
- explain which Requirement or protocol operation cannot currently bind;
- preserve the same Spell semantics across different Familiar dialects.

A Familiar still cannot self-certify authority, acceptance, persistence, effect confirmation, Mana settlement, or any other privileged runtime fact.

## Deliberately outside 0.3

These remain outside the portable declaration because current repository evidence has not established a stable contract shape for them:

- live State and CAST observations;
- Stats, standing, grade, and learned Scaling;
- portable Spell level semantics;
- Mana allocation/settlement fields;
- wall-clock scheduling;
- implementation-specific credentials or capability receipts.

They are not excuses to defer concrete runtime integration: when an Effect needs one of these today, it must bind an existing Environment/Cast protocol or fail closed.

## Compatibility

0.3 is intentionally not wire-compatible with 0.2. In particular:

- generic `limits` remains removed;
- Authority is a before Requirement;
- ordinary Requirements require `check` + `binding`;
- structured Requirements require exact `binding` selectors;
- Scope explicitly requires effect-path enforcement;
- typed interfaces, typed protocol operations, runtime contracts, and implementation suggestions are new.

FORMAT 0.2 remains Current until 0.3 is explicitly adopted.
