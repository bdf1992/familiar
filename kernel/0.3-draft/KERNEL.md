# Agent Spells Kernel 0.3 — Draft

Status: draft derived from the 0.3 FORMAT validation candidate. It does not replace the current reference Kernel yet.

The Kernel reads a Spell declaration, resolves one requested Effect against current reality, governs execution through a bound Technique, and emits CAST. It owns runtime truth; the declaration owns portable claims.

## Inputs to one cast

A cast requires:

- a validated Spell declaration and version;
- one selected Effect;
- a Caster identity understood by the host;
- a concrete target supplied or resolved by the host;
- a Technique binding capable of attempting the Effect;
- zero or one Familiar in the current draft; Familiar participation is optional and advisory.

The Kernel forbids a Familiar, Technique, or caster message from changing the Effect contract after selection.

## Requirement phases

The 0.3 draft makes phase part of the runtime contract.

### Before

Before Requirements decide whether execution may begin.

The reference mechanisms are:

- ordinary Requirement checker;
- Authority resolver backed by the host/security environment;
- Scope resolver plus the declared `max_items` bound.

The Kernel must refuse closure when a required observer/resolver/checker is absent, returns a negative result, or cannot produce a trustworthy current answer.

This forbids best-effort execution when the declaration says a condition is required.

### During

During Requirements govern effectful execution while it is happening.

The reference mechanisms are:

- Cost meter for named integer resources;
- execution Duration containment.

A Cost meter must reject the next charge before consumption would cross the declared ceiling. A Duration-capable binding must stop or contain execution at the finite bound.

This forbids after-the-fact accounting from masquerading as enforcement.

### After

After Requirements determine whether the declared Effect can be counted as resolved.

If effectful execution began, the Kernel should perform required post-observation even when the Technique reports failure or raises. Executor success is evidence about execution, not proof of the Effect.

An unresolved after Requirement becomes a residual. This forbids a partial or unverifiable result from being reported as fully resolved.

## Closure

Closure is the decision immediately before effectful execution.

A cast closes only when:

- the Spell and selected Effect are structurally valid;
- the target can be resolved enough for declared Requirements;
- any supplied Familiar is valid;
- required Telemetry is available and fresh enough;
- all before Requirements are satisfied;
- every declared during Requirement has an enforcement mechanism available in the selected Technique/runtime path.

Otherwise closure is refused and the Technique must not run.

### Current implementation gap

The reference tests prove that participating Technique bindings can enforce Cost and Duration. They do **not** yet provide a portable capability declaration proving that an arbitrary bound Technique supports those mechanisms before closure.

Until that exists, the 0.3 draft must treat Technique enforcement support as an unresolved Kernel requirement. A production runtime must not assume that passing a timeout or meter object means the Technique honors it.

## Technique binding

A Technique is implementation material, not part of `SPELL.md` semantics.

The host binds an Effect to a Skill, MCP tool sequence, script, service, or other executable implementation. Rebinding the Technique must not change the Spell declaration.

A binding must declare or demonstrate which runtime mechanisms it can participate in, especially:

- required Telemetry sources;
- ordinary checkers supplied by the host/implementation;
- Scope resolution;
- Cost meters/resources;
- Duration containment.

The Kernel forbids selecting a binding that cannot satisfy the Effect's required mechanisms unless another binding or host layer supplies them.

## Familiar participation

A Familiar may alter guidance representation, attention, or recommendations. It may not:

- grant Authority;
- widen Scope;
- increase Cost or Duration ceilings;
- change the selected Effect or its Requirements;
- manufacture Telemetry or postconditions.

A cast with no Familiar is valid when all other Requirements are satisfied.

This preserves one contract for human, agent, service, and machine-to-machine casting.

## Execution observations

CAST must preserve observations attributable to the exact Requirement ids declared in `SPELL.md`.

At minimum the 0.3 record supports:

- `before` Requirement results;
- `during` Cost/Duration results;
- `after` Requirement results;
- Telemetry observations with provenance/freshness where material;
- execution result/failure distinct from effect confirmation.

The record must retain the concrete target. This forbids a receipt that claims an Effect without saying what the Effect was applied to.

## Outcome

The current draft uses:

- `resolved` — execution completed and all required after conditions are satisfied;
- `partial` — execution occurred but at least one required after condition remains unresolved or negative without an execution/containment failure that makes the attempt failed;
- `failed` — effectful execution failed, a during Requirement was violated, or a required safety condition was violated after execution;
- no outcome when closure is refused because effectful execution never began.

The exact outcome rule should remain deterministic and published by the Kernel. A Technique may report its own status, but cannot assign the final outcome.

## Residuals

Residuals record declared Effect conditions that remain unresolved plus material execution failures that prevent the intended Effect from being established.

Residuals are not a general log. They forbid downstream consumers from treating an incomplete result as indistinguishable from a complete one.

## State

The Kernel may maintain transient cast context needed to connect observations, meters, Technique execution, and postconditions. Live context is not Spell declaration data.

No durable Spell State contract is standardized in 0.3 draft because current fixtures do not justify one. If a future Effect requires state across casts, that requirement must be tested before adding a portable state schema.

## CAST

CAST is the receipt. The 0.3 draft record contains:

- Spell name/version;
- cast id;
- Caster;
- target;
- optional Familiar reference and guidance;
- selected Effect;
- closure decision/reasons;
- before/during/after observations;
- execution result where available;
- outcome;
- residuals.

CAST must be machine-consumable and must not contain private chain-of-thought.

## Kernel conformance requirements currently supported by evidence

The reference implementation/fixtures demonstrate:

- malformed Spell/Familiar rejection;
- required Telemetry gating;
- Authority refusal;
- Scope refusal before Technique execution;
- Cost ceiling enforcement before excess consumption;
- execution Duration containment through a participating subprocess binding;
- executor failure followed by post-observation;
- after Requirement verification independent of executor success;
- requirement identity preserved into candidate CAST;
- machine Caster CAST serialization;
- Familiar dialect variation with unchanged Spell behavior.

These are mechanics tests. They do not establish Spell standing.

## Next Kernel validation

1. Define a Technique binding capability declaration sufficient for closure to know whether required Cost/Duration/Scope mechanisms are actually enforceable.
2. Bind the 0.3 draft to the real workspace-tidy Technique rather than only the synthetic bounded-work candidate.
3. Add an observation-window Duration fixture.
4. Test a second Technique for the same Effect to confirm the declaration remains invariant.
5. Test one MCP-backed Technique to validate composition with MCP execution and authorization rather than only local subprocesses.
6. Revisit durable State only when a concrete Effect requires cross-cast state.
