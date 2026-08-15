# Spell Core Shape — Validation Pass

Date: 2026-08-15.

This note records the current Spellcraft/Owl pass over the shape of a Spell. It does **not** change FORMAT 0.2. `format/SPECIFICATION.md` remains normative until the candidate structure is exercised and versioned.

## Survival rule

A portable Spell field survives only if it is Technique-independent and at least one is true:

1. it materially helps selection or inspection;
2. it gates whether an Effect may execute;
3. it constrains effectful execution through a host-checkable boundary;
4. it determines whether the declared Effect occurred.

If none apply, the field is decoration and stays outside `SPELL.md`.

## What now clearly survives

### Description

Discovery and inspection text. It is author-asserted and never effect evidence.

### Effect

The runtime change or resulting condition being attempted. Without an Effect there is nothing for the Kernel to govern or confirm.

### Telemetry

Current observations needed to resolve casting Requirements. Freshness belongs here when stale state can change the decision.

### Requirements

Requirements are now the validation spine. A before Requirement gates closure. An after Requirement determines effect confirmation and becomes a residual when unresolved.

The external workspace-tidy fixture proves that an observable preservation invariant does not need a generic Limit: `preserve-unmarked` moved to an after Requirement, retained the same byte-for-byte external guarantee, and CI remained green.

Authority is semantically a before Requirement but still requires a privileged host/security resolver. Caster prose, Familiar guidance, Skill instructions, and executor output cannot self-certify authority.

## Concerns that have runtime mechanics but have not earned peer FORMAT fields

### Duration

The Kernel can hand a finite execution bound to a Technique binding. A subprocess fixture exceeds the bound and is terminated; CAST records failed execution and residuals; post-execution observation still runs.

This proves Duration is governable when the binding can enforce it. It does not prove that `duration:` deserves a peer field in `SPELL.md`.

Duration may instead be a structured before/execution Requirement carrying a machine-readable bound.

### Cost

The Kernel can hand a named resource ceiling to a Technique binding. A fixture with `tool_calls: 1` charges once, performs one action, then has the second charge rejected before the second action occurs. CAST records used/max cost and the failure residual.

This proves Cost is governable when the effectful resource participates in the meter. It does not prove that `cost:` deserves a peer field in `SPELL.md`.

Cost may instead be a structured Requirement carrying a resource and ceiling.

### Scope

The Kernel can resolve a target into concrete items, compare the count to a bound, record the resolved target/items/count, and refuse before Technique execution when the bound is exceeded. The scope fixture is green.

The important result is that this behavior is currently recorded as a before Requirement observation (`scope-max-items`). That means Scope has demonstrated a real casting concern but has **not** demonstrated a unique declaration job separate from Requirements.

If Scope becomes a portable concept, the declaration must carry the machine-readable boundary and CAST must retain the resolved target/reach. A host-local target name alone is not portable Scope.

## Concerns that currently collapse

### Domain

The Domain challenge is green. An effect that is only valid for filesystem targets was expressed entirely as a before Requirement (`domain-compatible`). A queue target was refused before Technique execution.

Therefore Domain has no demonstrated unique runtime job. If Domain remains, it should be optional discovery/inspection metadata. Runtime compatibility belongs to Requirements.

### Generic Limit

Generic Limit no longer has a demonstrated unique job:

- reach/quantity -> Scope concern;
- resource ceiling -> Cost concern;
- time ceiling -> Duration concern;
- preservation/safety/result-state invariant -> Requirement.

FORMAT 0.2 still supports `limits` for compatibility. Current evidence argues against carrying generic `limits` into the next candidate format unless a fixture finds a constraint that cannot be represented more precisely.

## What remains outside SPELL

### Instructions

Instructions belong to a Skill, Technique, MCP tool/service binding, or host. They explain how an Effect is attempted; they are not the Effect contract.

### State

Live state belongs to runtime/CAST. State that matters to validity is observed through Telemetry and tested through Requirements. A future persistent-state case may justify a declaration schema, but no current fixture does.

### Stats

Stats are aggregates over CAST records, not author claims.

### Scaling

Scaling is learned from repeated CAST records across changing Scope, Cost, Duration, and outcomes. A supported hard boundary may later be written into a new declaration version; scaling itself is not currently declaration truth.

## Current smallest hypothesis

The validation now suggests that the portable semantic core may be smaller than the original field list:

- identity/version metadata;
- Description;
- Telemetry declarations;
- Effects;
- Requirements attached to each Effect.

Scope, Cost, Duration, Domain compatibility, Authority, and observable invariants may all be **forms of Requirements** rather than peer top-level concepts. They can still have dedicated Kernel mechanisms where enforcement requires one.

This is a hypothesis, not FORMAT 0.3 yet.

## Requirement structure to test next

The next candidate should test whether one Requirement surface can carry both ordinary checks and machine-readable specialized constraints without becoming an untyped dumping ground. Example shape:

```yaml
requirements:
  before:
    - id: target-observable
      description: The requested target is observable.

    - id: write-authority
      authority: workspace.write

    - id: bounded-scope
      scope:
        max_items: 2

    - id: tool-budget
      cost:
        resource: tool_calls
        max: 1

    - id: execution-time
      duration:
        execution_max_ms: 25

  after:
    - id: disposable-absent
      description: No disposable file remains.

    - id: preserve-unmarked
      description: Every pre-existing unmarked file remains byte-identical.
```

No new protocol nouns are introduced here. Authority, Scope, Cost, and Duration are existing concerns being tested as structured Requirement forms.

## Declaration / CAST symmetry

| Declaration concern | CAST evidence |
|---|---|
| Effect | attempted Effect and outcome |
| Telemetry | observations with provenance/freshness |
| ordinary Requirement | before/after check result |
| Authority Requirement | host authorization result |
| Scope Requirement | resolved target/items/count/bound |
| Cost Requirement | used resource and ceiling |
| Duration Requirement | applied bound and material timing |
| Description | no authoritative runtime counterpart |

## Evidence status

Validated in current tests/fixtures:

- real filesystem Effect independently observed after Skill execution;
- authority refusal before Technique execution;
- malformed Familiar refusal;
- Familiar dialect changes guidance but not Spell behavior;
- executor failure preserves post-observation and residuals;
- machine caster receives machine-consumable CAST;
- execution Duration can be contained by a participating Technique binding;
- Cost can reject the next metered unit before consumption;
- Scope can refuse an over-broad resolved target before execution;
- Domain compatibility can be expressed as a before Requirement;
- preservation Limit can be replaced by an after Requirement with no lost guarantee.

Not yet validated:

- Scope/Cost/Duration/Authority values arriving from one portable candidate Requirement structure rather than cast/host configuration;
- observation-window Duration;
- temporary effect lifetime;
- portable resource naming/units for Cost;
- durable Spell State;
- aggregation into Stats/Scaling or Spell standing.

## Next validation sequence

1. Create an **experimental candidate declaration** in `validation/` that nests Authority, Scope, Cost, and Duration under Requirements while keeping FORMAT 0.2 normative.
2. Add a candidate adapter that derives existing Kernel enforcement inputs from that declaration; the caller must not separately pass the bounds.
3. Run one cast where all structured Requirements pass and one where Scope/Cost/Duration independently fail.
4. If that works without semantic ambiguity, draft FORMAT 0.3 around the smaller shape and remove generic Limit.
5. Derive the matching CAST shape so target/scope and material bound evidence are first-class rather than hidden inside incidental host configuration.
6. Only after multiple real casts exist, revisit State, Stats, Scaling, and standing.

Working proposition:

> A Spell declares an Effect and the Requirements under which that Effect may count. CAST records what happened. The Kernel owns the difference.
