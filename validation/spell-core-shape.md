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

### Cost — survives conditionally

**Meaning:** measurable resource bounds material to whether or how an Effect may run.

**Why it may belong:** the Kernel can gate a cast on declared budgets and record actual use in CAST.

**Forbids:** exceeding a declared measurable resource ceiling or reporting author estimates as observed usage.

Candidate resources include tool calls, bytes written, files changed, compute, money/quota, or required approvals where the host can meter them.

If no host meter exists, the proposed Cost is not yet enforceable and must remain outside FORMAT.

### Duration — survives conditionally

**Meaning:** measurable time bounds that materially constrain execution, confirmation, or temporary effect lifetime.

**Why it may belong:** the Kernel can use clocks/timeouts and record actual timing.

**Forbids:** execution or observation continuing beyond a declared finite bound without an explicit unresolved outcome.

Candidate cases:

- maximum execution time;
- maximum observation window for an after Requirement;
- lifetime of an explicitly temporary Effect.

Actual timestamps and elapsed duration belong in CAST.

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
- resource ceilings -> Cost;
- time ceilings -> Duration;
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
| Cost | actual measured resource use |
| Duration | actual start/end/elapsed/observation timing |
| Description | no authoritative runtime counterpart |

If a new declaration field has no plausible runtime counterpart and does not materially improve discovery, Spellcraft should challenge it.

## Evidence from workspace-tidy

The first external-effect fixture already supports:

- Effect: `tidy` is independently investigated after script execution;
- Telemetry: before/after filesystem manifests are observed;
- Requirements: the postcondition is independent of process exit status;
- Scope/target: the host operates on a concrete temporary workspace;
- Authority: denied write authority prevents Technique execution;
- CAST: the runtime emits a machine-consumable record.

It does not yet validate Cost, Duration, Domain as an enforceable portable field, or learned Scaling/Stats.

## Next validation sequence

Do not revise FORMAT from vocabulary alone. Exercise the candidate fields in this order:

1. **Duration fixture:** add an Effect with a short execution or observation bound; prove the Kernel stops waiting and emits an unresolved/failed CAST rather than hanging or claiming success.
2. **Cost fixture:** meter one concrete resource (recommended: number of files written or tool invocations); prove over-budget execution is refused or cannot resolve.
3. **Scope fixture:** request a target wider than the declared bound; prove the Kernel refuses before the Technique can touch the excess target.
4. **Domain fixture:** bind the same Effect request to one compatible and one incompatible target/environment; determine whether a portable Domain identifier provides real value beyond a before Requirement.
5. **Requirements migration:** rewrite workspace-tidy's generic `preserve-unmarked` Limit as an after Requirement and verify the same external-effect guarantees.
6. If 1–5 pass, draft FORMAT 0.3 and derive CAST 0.3 from the new declaration shape.
7. Only after multiple real CAST records exist, design Stats/Scaling aggregation. Do not add either to `SPELL.md`.

The working proposition is:

> A Spell declares the bounded conditions of an Effect. CAST records what happened under those conditions. The Kernel owns the difference between the declaration and the observation.
