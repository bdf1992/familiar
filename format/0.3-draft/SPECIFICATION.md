# Agent Spells Format 0.3 — Draft

Status: draft derived from validation fixtures on 2026-08-15. FORMAT 0.2 remains the current compatibility baseline until this draft is adopted.

## Purpose

`SPELL.md` declares Effects and the Requirements under which those Effects may be attempted and counted as resolved. It does not select an implementation, contain live runtime state, or claim standing.

The 0.3 draft removes generic `limits` and the separate `authority` field from the 0.2 shape. Authority, Scope, Cost, Duration, safety invariants, compatibility checks, and postconditions are represented as Requirements with phase-appropriate structure.

## Portable frontmatter

```yaml
---
spell_format: "0.3"
name: bounded-work
version: "0.1.0"
description: Attempt bounded work and verify its result.
telemetry: []
effects:
  - id: act
    description: Perform the requested bounded action.
    telemetry: []
    requirements:
      before:
        - id: target-observable
          description: The requested target is observable.
        - id: write-authority
          authority: workspace.write
        - id: bounded-scope
          scope:
            max_items: 2
      during:
        - id: tool-budget
          cost:
            resource: tool_calls
            max: 1
        - id: execution-time
          duration:
            execution_max_ms: 50
      after:
        - id: effect-confirmed
          description: The requested effect is observable as complete.
---
```

The optional Markdown body is human guidance only. It cannot satisfy a Requirement.

## Required top-level fields

### `spell_format`

Declares the FORMAT version. A host must reject versions it does not support. This forbids silently interpreting a declaration under incompatible semantics.

### `name`

Stable portable identifier used in catalogs and CAST. This forbids anonymous execution records that cannot be tied to a declaration.

### `version`

Version of the declaration. This forbids materially different contracts from being treated as the same Spell definition.

### `description`

Author-asserted discovery and inspection text. It helps selection but is never runtime evidence.

### `telemetry`

Declares named current observations that Effects may require. A telemetry declaration has an id, description, and optional maximum age. This forbids substituting assumed or stale state where current observation is required.

### `effects`

Declares one or more Effects. Each Effect has an id, description, telemetry references, and Requirements. An Effect is the change or resulting condition the runtime attempts and investigates.

## Requirements

Requirements are phase-specific. Every Requirement has a stable id. The runtime record must preserve that id so declaration and CAST can be compared directly.

### `before`

A before Requirement must be satisfied for execution to close.

The draft supports three validated forms:

**Ordinary check**

```yaml
- id: target-observable
  description: The target can be observed.
```

A host supplies the checker. If no checker exists or the check is negative, execution is refused. This forbids prose confidence from replacing a real precondition check.

**Authority**

```yaml
- id: write-authority
  authority: workspace.write
```

The host/security environment resolves the permission. A caster, Familiar, Skill, executor, or declaration cannot self-certify it. This forbids a Spell from widening the host's authorization model.

**Scope**

```yaml
- id: bounded-scope
  scope:
    max_items: 2
```

The host resolves the concrete target into items and refuses before execution when the count exceeds the declared bound. CAST retains the resolved target, item count, and bound. This forbids a compliant Technique from silently widening the requested reach.

The draft standardizes only `max_items` because that is the only Scope form exercised by the current fixtures. It does not claim a universal domain-specific Scope language.

### `during`

A during Requirement is governed while effectful execution is occurring. Declaring the budget is insufficient: the Technique/runtime path must actually participate in the enforcement mechanism.

**Cost**

```yaml
- id: tool-budget
  cost:
    resource: tool_calls
    max: 1
```

The runtime makes a named integer budget available to the Technique binding. The next metered unit must be denied before it would exceed the ceiling. CAST records used/max values against the Requirement id.

This forbids after-the-fact counting from being presented as budget enforcement.

The draft does not standardize arbitrary currencies or units. A resource name is meaningful only when the host and Technique share a real meter for it.

**Duration**

```yaml
- id: execution-time
  duration:
    execution_max_ms: 50
```

The runtime passes the bound to a Technique binding capable of containing execution. CAST records material timing against the Requirement id.

This forbids a compliant binding from ignoring a finite execution bound and later calling the Effect resolved merely because execution eventually returned.

Only execution duration is standardized in this draft. Observation-window duration and temporary Effect lifetime remain unvalidated.

### `after`

An after Requirement determines whether the Effect can be counted as resolved.

```yaml
- id: preserve-unmarked
  description: Every pre-existing unmarked file remains byte-identical.
```

A host independently checks the resulting state. If an after Requirement is negative or unavailable, the Effect cannot be fully resolved and CAST carries the unresolved condition as a residual.

This forbids executor success from substituting for effect confirmation.

## Removed from the 0.2 candidate shape

### Generic `limits`

Removed. Current evidence gives its former jobs to more precise Requirement forms: Scope, Cost, Duration, and ordinary before/after Requirements. The real workspace-tidy fixture preserved the same external safety guarantee after its only Limit became an after Requirement.

### Separate effect `authority`

Removed as a peer field. Authority is a before Requirement with a privileged host resolver.

## Not in the portable format

- **Domain as runtime semantics** — compatibility was fully enforced as a before Requirement in the Domain fixture. Domain may be reconsidered later as optional discovery metadata if catalogs demonstrate a need.
- **Instructions** — belong to Skills, Techniques, MCP tools/services, or host bindings.
- **live State** — belongs to runtime/CAST; relevant current state is observed through Telemetry and Requirements.
- **Stats** — derived from multiple CAST records.
- **Scaling** — learned from Stats and repeated casts; supported hard boundaries may be reflected in a later declaration version.
- **standing/level/grade** — execution-derived and outside this draft.
- **Familiar preferences** — Familiar is an optional caster dialect/judgment artifact and cannot alter Spell semantics.

## Semantic validation

A conforming validator must reject:

- duplicate telemetry ids;
- duplicate Effect ids;
- duplicate Requirement ids within one Effect across all phases;
- Effect telemetry references that do not resolve;
- more than one Scope Requirement for the same Effect in this draft;
- more than one execution Duration Requirement for the same Effect in this draft;
- duplicate Cost resource names for the same Effect;
- Cost or Duration declarations placed in `before` or `after`;
- Authority or Scope declarations placed in `during` or `after`.

## Runtime boundary

FORMAT describes what must be governed. It does not guarantee that a host can govern it.

A host that cannot provide a declared observer, checker, authority resolver, Scope resolver, Cost meter, or Duration containment mechanism must refuse the affected cast rather than silently weakening the declaration.

## Evidence supporting this draft

The current reference suite demonstrates:

- before ordinary Requirements;
- host-resolved Authority;
- Scope refusal before Technique execution;
- Cost denial before the next metered action;
- Duration containment of a subprocess;
- independent after Requirements;
- post-observation after executor failure;
- target retention in the candidate CAST;
- machine caster records;
- Familiar guidance that changes representation without changing Spell behavior.

These tests establish mechanics, not Spell standing.
