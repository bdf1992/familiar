# Agent Spells Casting 0.4 — Draft

Status: draft derived from the 0.3 FORMAT/KERNEL validation work. This document defines runtime process, not portable Spell fields. FORMAT 0.3 remains a draft and the current reference implementation remains compatible with 0.2.

## Governing rule

Every Spell is cast through the same runtime process regardless of later standing, level, implementation kind, caster kind, or Familiar.

The Spell changes which Requirements are present. It does not change the casting law.

The Kernel permits effectful execution only when the current caster, target, environment, and Technique Binding can satisfy the declared contract. If the runtime cannot resolve or enforce a required condition, closure is refused.

This forbids prose obedience from being counted as enforcement.

## Casting process

### 1. Resolve the invocation

The runtime resolves:

- Spell name/version;
- selected Effect;
- Caster;
- requested target;
- optional Familiar;
- candidate Technique Binding.

The declaration is not modified during casting.

This forbids a Technique, Familiar, or caster message from changing the Effect contract after selection.

### 2. Validate the declaration and participants

The runtime validates the Spell and any supplied Familiar, then verifies that the Technique Binding realizes the exact Spell version and Effect being requested.

This forbids executing a different implementation contract merely because it has a similar description.

### 3. Build the Requirement plan

The runtime reads all declared Telemetry and Requirements for the selected Effect.

Before Requirements must be resolvable before effectful execution. During Requirements must have an enforcement path available during effectful execution. After Requirements must have an observation/check path available after execution.

This forbids discovering only after execution that a required check or control mechanism never existed.

### 4. Verify runtime and Technique support

Before evaluating the caster-specific conditions, the runtime verifies that the current host/environment and selected Technique Binding can support every required mechanism.

For the 0.4 draft:

- Authority requires a host authority resolver and a Technique path that can operate under that resolved authority boundary;
- Scope requires a target resolver and an effectful path constrained to the resolved Scope;
- Cost requires a host/runtime meter and a Technique path that participates in that meter;
- execution Duration requires a clock/containment mechanism and a Technique path that can be stopped or contained by it;
- ordinary Requirements require registered checkers;
- Telemetry requires registered observers.

A binding declaration is structural input, not proof that its implementation is truthful. Conformance tests must establish that the advertised mechanisms are actually honored.

This forbids closure when the runtime only hopes that the Technique will follow a Requirement.

### 5. Resolve target and current observations

The runtime resolves the concrete target/Scope and acquires required Telemetry with provenance and freshness where declared.

This is where an invocation such as "these files" becomes a concrete bounded target that later CAST can record.

This forbids an Effect receipt that cannot identify what was actually acted upon.

### 6. Evaluate before Requirements

The runtime evaluates all before Requirements, including target compatibility, Authority, Scope, material availability, or other declared preconditions.

If any required condition is unavailable, denied, violated, or otherwise unsatisfied, closure is refused and no effectful Technique execution occurs.

A before check may establish availability without consuming a resource. If a resource is meant to be consumed only during execution, availability and consumption are separate Requirements at their appropriate phases.

This forbids paying or mutating merely because an invocation was attempted when the Spell declares that consequence later in casting.

### 7. Closure

Closure is the single authorization decision immediately before effectful execution.

A cast closes only when:

- declaration and participants are valid;
- the binding realizes the selected Effect;
- the environment exposes every required observer/checker/control mechanism;
- the binding can participate in every required effect-path control;
- required Telemetry is available/fresh;
- target/Scope is resolved;
- all before Requirements are satisfied.

If any item is false, closure is refused.

This forbids best-effort execution under a weakened contract.

### 8. Execute while governing during Requirements

Only after closure may the Technique perform effectful work.

During Requirements are active controls, not reminders. Examples include:

- charging a metered component/resource at the declared point of consumption;
- refusing the next tool call when a Cost ceiling would be crossed;
- containing execution at a Duration boundary;
- keeping effectful operations inside the resolved Scope and Authority boundary.

If a during Requirement is violated or its enforcement mechanism disappears, execution is stopped or contained where possible and the cast cannot resolve normally.

This forbids after-the-fact accounting from masquerading as enforcement.

### 9. Observe after execution

If effectful execution began, the runtime performs required post-observation even when the Technique reports failure, times out, or raises.

This detects partial effects and changes that occurred before failure.

This forbids treating executor failure as evidence that nothing changed.

### 10. Evaluate after Requirements

The runtime evaluates declared after Requirements from current observations independently of the Technique's own success report.

An unresolved or negative required postcondition prevents full resolution and is retained in residuals.

This forbids implementation success from substituting for Effect confirmation.

### 11. Classify and emit CAST

The Kernel assigns the outcome and emits one machine-consumable CAST containing at least:

- Spell name/version;
- Effect;
- Caster;
- concrete target;
- optional Familiar reference/guidance;
- Technique Binding identity/version;
- closure decision/reasons;
- before/during/after observations tied to Requirement ids;
- execution result/failure where available;
- outcome;
- residuals.

This forbids execution history that cannot be compared across Techniques or later audited.

## Conditional casting

The universal process is intentionally conditional.

A Spell with no Cost Requirement does not invent a Cost step. A Spell with no Familiar does not invent one. A Spell with material availability and consumption may check availability before closure and consume the material during execution. A temporary Effect may later justify an after/Duration form when evidence supports it.

The law is therefore not a fixed list of fantasy actions. It is a fixed ordering for resolving and enforcing whichever declared Requirements exist.

## Environment control boundary

The Kernel does not need to implement every observer, permission system, meter, sandbox, MCP server, filesystem, or service itself. It must, however, bind to concrete environment mechanisms and refuse closure when required control is unavailable.

For consequence-bearing Requirements, a check alone is insufficient when the effectful path can bypass the checked boundary. In particular:

- Scope preflight without Scope-constrained execution is not full Scope enforcement;
- Authority resolution without an execution path bounded by that authority is not full Authority enforcement;
- Cost measurement after uncontrolled execution is not Cost enforcement;
- elapsed-time measurement after an uncontainable executor returns is not Duration enforcement.

The 0.4 release must prove these distinctions through Technique Binding and runtime conformance tests.

## What 0.4 must prove

0.4 should not add new Spell semantics merely to advance the version number. It must demonstrate that:

1. the Kernel refuses closure when a required effect-path mechanism is absent from the selected Technique Binding or environment;
2. the Kernel records the selected Technique Binding in CAST;
3. one real Spell/Effect is realized by two different Technique Bindings without changing SPELL.md;
4. Scope cannot be widened by the participating reference execution path after closure;
5. Cost and Duration remain actively governed during execution;
6. one MCP-backed Technique can participate without replacing MCP authorization, schemas, errors, or transport semantics;
7. Familiar changes guidance only and cannot alter the closure contract.

These mechanics are prerequisites for later standing/reliability work. They do not establish Spell standing by themselves.
