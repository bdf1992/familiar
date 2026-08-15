# Spell Core Shape — Validation Pass

Date: 2026-08-15.

This note records the current Spellcraft/Owl pass over the shape of a Spell. It does **not** change FORMAT 0.2. `format/SPECIFICATION.md` remains normative until the candidate fields below are exercised by fixtures and adopted in a versioned format revision.

## Survival rule

A portable Spell field survives only if it is Technique-independent and at least one of the following is true:

1. it materially helps selection/inspection;
2. it gates whether an Effect may execute;
3. it constrains effectful execution through a host-checkable boundary;
4. it determines whether the declared Effect occurred.

A field that satisfies none of these is decoration and stays outside `SPELL.md`.

## Candidate shape

### Domain — survives conditionally

**Meaning:** the kind of target/environment in which the Spell's Effects have meaning.

**Why it may belong:** a host can refuse execution when the resolved target does not belong to a declared Domain.

**Forbids:** silently applying an Effect to an environment for which its requirements and observations have no defined meaning.

**Open requirement:** the format needs a portable domain identifier strategy or must leave Domain author-asserted. Until a host can resolve it, Domain is not ready to become a required FORMAT field.

### Description — survives

**Meaning:** discovery and inspection text.

**Why it belongs:** enables catalog selection and human/machine inspection.

**Forbids:** nothing at runtime; it is explicitly author-asserted and must never count as effect evidence.

### Effect — survives

**Meaning:** a runtime change or resulting condition that can be attempted and investigated after execution.

**Why it belongs:** without an Effect there is nothing for the Kernel to govern or confirm.

**Forbids:** classifying instructions, capability descriptions, or executor success as the effect itself.

### Scope — survives conditionally

**Meaning:** what a selected Effect may reach and how much.

**Why it may belong:** the Kernel can resolve a concrete requested target against a portable bound before execution.

**Forbids:** a Technique silently affecting targets outside the resolved cast.

**Open requirement:** Scope must be expressible without embedding domain-specific implementation data in FORMAT. Candidate implementations should prove at least target identity plus one quantity/range boundary.

### Requirements — survives

**Meaning:** conditions evaluated before execution and conditions evaluated afterward for effect confirmation.

**Why it belongs:** Requirements are the main bridge between declaration and observable runtime truth.

**Forbids:** closure when a before Requirement is not satisfied, and successful resolution when an after Requirement remains unconfirmed.

Authority is treated as a before Requirement but must be resolved by the host/security environment, never by Familiar guidance, caster prose, or executor self-report.

### Telemetry — survives

**Meaning:** current observations needed to resolve Requirements, Scope, Domain, or other execution gates.

**Why it belongs:** the Kernel must know which current state must be observed and when freshness matters.

**Forbids:** substituting stale or assumed state where the declaration requires a current observation.

### Cost — runtime mechanism validated; FORMAT field not yet promoted

**Meaning:** measurable resource bounds material to whether or how an Effect may run.

**Validated behavior:** the Kernel can provide a Technique binding with a named integer ceiling. The reference fixture gives `tool_calls` a ceiling of one. The Technique charges once, performs the first action, then attempts to charge again. The second charge is rejected before the second action occurs. CAST records used and maximum cost, execution fails, and a residual records the exceeded ceiling. CI passes.

**Important boundary:** Cost is governable only when the effectful resource passes through a runtime/Technique path that participates in the meter. Counting resource use after uncontrolled execution is observation, not enforcement.

**Forbids:** a compliant binding consuming another metered unit after the declared ceiling would be exceeded, or reporting author estimates as observed usage.

Still unvalidated:

- a Cost declaration arriving from portable `SPELL.md`;
- host-independent resource naming/units;
- externally metered resources such as money, quota, compute, or bytes written;
- whether some proposed Cost categories are better represented as Scope or Requirements.

Cost has earned a runtime mechanism. It has not yet earned a required FORMAT field.

### Duration — runtime mechanism validated; FORMAT field not yet promoted

**Meaning:** measurable time bounds that materially constrain execution, confirmation, or temporary effect lifetime.

**Validated behavior:** the Kernel accepts an execution duration bound and passes it to the Technique binding. The reference fixture uses a subprocess that exceeds the bound; the binding terminates the subprocess, the Kernel records failed execution with the bound and measured elapsed time, post-execution telemetry still runs, and CAST resolves to `failed` with residuals. CI passes.

**Important boundary:** the Kernel can only govern execution Duration when the Technique binding can actually enforce the bound. Merely measuring elapsed time after an uncontrolled Technique returns is observation, not containment.

**Forbids:** execution continuing beyond a declared finite execution bound when the binding claims duration support, and reporting an over-duration execution as resolved merely because the executor eventually returned.

Still unvalidated:

- a Duration value arriving from portable `SPELL.md` rather than cast/runtime input;
- observation windows for after Requirements;
- lifetime of explicitly temporary Effects.

Actual timing should appear in CAST only when timing is material to the cast. The Duration regression test caught and removed incidental `elapsed_ms` from ordinary casts so existing CAST records remain stable when no Duration participates.

### Scaling — does not survive as an author-declared core field

**Meaning:** relationship among Scope, Cost, Duration, outcome, and reliability as casts vary.

**Why it does not belong yet:** this is learned from multiple CAST records rather than known from declaration alone.

**Forbids:** a spellcrafter claiming scaling behavior as runtime truth.

When evidence supports a useful hard boundary, a new Spell version can encode that boundary through Scope, Cost, Duration, or Requirements.

### Instructions — does not belong in SPELL

Instructions belong to a Skill, Technique, MCP implementation, service, or host binding.

**Forbids:** binding portable Spell semantics to one implementation procedure.

### State — does not belong in SPELL as live data

Current execution state belongs to CAST/runtime. Required starting or resulting state is represented through Telemetry and Requirements.

**Forbids:** a portable declaration pretending that live environment state is static declaration data.

### Stats — do not belong in SPELL

Stats are derived from CAST records: counts, outcome rates, costs, durations, scale behavior, and other aggregates.

**Forbids:** author-declared runtime history.

## Limits audit

FORMAT 0.2 contains a first-class `limits` field. This pass suggests it may be an intermediate abstraction rather than a core Spell property.

Candidate absorption:

- reach/target boundaries -> Scope;
- resource ceilings -> Cost, if Cost survives FORMAT validation;
- time ceilings -> Duration, if Duration survives FORMAT validation;
- invariants such as preservation/safety conditions -> Requirements.

The workspace-tidy `preserve-unmarked` limit can be rewritten as an after Requirement asserting that every unmarked pre-existing file remains present and byte-identical. This is more directly observable than calling it a generic Limit.

Do not remove `limits` from FORMAT until a migrated fixture proves the replacement is at least as expressive and enforceable.

## Declaration / CAST symmetry

A useful test for every candidate field is whether CAST can record the runtime counterpart:

| SPELL declaration | CAST evidence |
|---|---|
| Domain | resolved target/environment |
| Effect | attempted Effect and resulting outcome |
| Scope | concrete resolved target/reach |
| Telemetry | observations actually obtained with provenance/freshness |
| Requirements | before/after check results |
| Cost | actual metered resource use when a real meter participates |
| Duration | actual bound plus measured timing when Duration participates |
| Description | no authoritative runtime counterpart |

If a new declaration field has no plausible runtime counterpart and does not materially improve discovery, Spellcraft should challenge it.

## Evidence from workspace-tidy and kernel fixtures

The first external-effect workspace-tidy fixture supports:

- Effect: `tidy` is independently investigated after script execution;
- Telemetry: before/after filesystem manifests are observed;
- Requirements: the postcondition is independent of process exit status;
- Scope/target: the host operates on a concrete temporary workspace;
- Authority: denied write authority prevents Technique execution;
- CAST: the runtime emits a machine-consumable record.

The Duration fixture additionally supports:

- a finite execution bound can be handed from Kernel to Technique binding;
- a compliant subprocess binding can contain over-duration execution;
- timeout does not erase post-execution observation;
- Duration evidence is omitted from casts where Duration is not involved.

The Cost fixture additionally supports:

- a named budget can be enforced before the next metered unit is consumed;
- used/max resource evidence can be retained in CAST;
- an exceeded Cost can fail execution without pretending the second action occurred;
- ordinary casts remain unchanged when no Cost participates.

It does not yet validate Domain as an enforceable portable field, Scope as a portable declaration, observation/effect-lifetime Duration, portable Cost resource semantics, or learned Scaling/Stats.

## Next validation sequence

Do not revise FORMAT from vocabulary alone. Continue in this order:

1. **Scope fixture:** request a target wider than the declared bound; prove the Kernel refuses before the Technique can touch the excess target.
2. **Domain fixture:** bind the same Effect request to one compatible and one incompatible target/environment; determine whether a portable Domain identifier provides real value beyond a before Requirement.
3. **Requirements migration:** rewrite workspace-tidy's generic `preserve-unmarked` Limit as an after Requirement and verify the same external-effect guarantees.
4. **Candidate declaration path:** if the prior structure still survives, introduce Scope, Cost, and Duration only in an experimental candidate declaration and prove the Kernel consumes them without host-specific cast configuration.
5. If the surviving candidate fields pass, draft FORMAT 0.3 and derive CAST 0.3 from the new declaration shape.
6. Only after multiple real CAST records exist, design Stats/Scaling aggregation. Do not add either to `SPELL.md`.

The working proposition is:

> A Spell declares the bounded conditions of an Effect. CAST records what happened under those conditions. The Kernel owns the difference between the declaration and the observation.
