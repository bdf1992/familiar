# Agent Spells Kernel 0.4 — Draft

Status: development draft. 0.4 extends the requirement-centered 0.3 work by defining the invariant casting process and the Technique Binding boundary. It does not establish Spell standing.

## Goal

0.4 must prove that the same Spell/Effect can be cast through different Techniques without weakening the declaration and that the Kernel refuses closure whenever the selected Technique/environment cannot enforce the declared contract.

The central distinction is:

- `SPELL.md` declares what must be true;
- Technique Binding identifies one implementation and the effect-path mechanisms it claims to support;
- the host/environment supplies concrete observers, resolvers, meters, containment, and authority controls;
- the Kernel decides whether those pieces are sufficient to close, governs execution, observes the result, and emits CAST.

This forbids using the Technique Binding as a second Spell declaration.

## Universal casting law

Every Spell follows the process in `CASTING.md`:

1. resolve invocation;
2. validate declaration, Caster, optional Familiar, and Technique Binding;
3. build the Requirement plan;
4. verify required runtime and Technique support;
5. resolve target and acquire required Telemetry;
6. evaluate before Requirements;
7. close or refuse;
8. execute while governing during Requirements and the resolved consequence boundaries;
9. observe after execution;
10. evaluate after Requirements;
11. classify and emit CAST.

No later Spell level or standing may bypass this process. More consequential Spells may have more Requirements; they do not get a different casting law.

## Technique Binding

A Technique Binding is runtime integration metadata for one implementation of one Spell version/Effect.

The 0.4 draft binding records:

- binding id/version;
- implementation kind (`skill`, `mcp`, `script`, `service`, or `host`);
- exact Spell name/version and Effect realized;
- whether the execution path participates in the Authority boundary;
- Scope mechanisms it participates in;
- named Cost resources it meters through the runtime;
- Duration containment mechanisms it supports.

The binding forbids substituting a merely similar Technique for the exact Effect contract.

### Binding declarations are not proof

A schema-valid binding can lie. Therefore:

- schema validation proves only the descriptor shape;
- closure matching proves only that required mechanism registrations are present;
- conformance fixtures prove that a reference binding actually honors those mechanisms;
- hard environmental isolation/sandboxing is needed when the runtime claims protection against an untrusted Technique that could bypass cooperative mechanisms.

This forbids treating `mechanisms.scope: [max_items]` as evidence that arbitrary code cannot touch other objects.

## Closure support matching

Before effectful execution, the Kernel derives the mechanisms demanded by the selected Effect and compares them against the current host/environment and Technique Binding.

### Ordinary Requirements

Every ordinary before/after Requirement needs a registered checker.

Missing checker -> refuse closure.

### Telemetry

Every declared telemetry id used by the Effect needs a registered observer.

Missing observer -> refuse closure.

### Authority

Authority requires both:

1. a host/security resolver that can decide the Caster's permission; and
2. an execution path constrained to the resulting Authority boundary.

Missing either -> refuse closure.

This forbids checking authorization with one identity and then executing with broader credentials.

### Scope

Scope requires both:

1. a resolver that turns the requested target into concrete bounded reach; and
2. an execution path constrained to that resolved reach.

Missing either -> refuse closure.

This forbids preflight Scope counting from being called enforcement when the Technique can later reach outside the resolved target.

### Cost

Cost requires a runtime meter and Technique participation for every declared resource.

The next metered unit must be denied before consumption would exceed the declared ceiling.

Missing participation -> refuse closure.

This forbids after-the-fact usage accounting from being called enforcement.

### Duration

Execution Duration requires a finite runtime clock/containment path plus Technique participation in cancellation/containment.

Missing containment -> refuse closure.

This forbids measuring elapsed time after an uncontainable executor returns and calling the duration bound enforced.

## Runtime/environment integration

The Kernel coordinates environment controls; it does not need to implement all of them itself.

Examples include:

- host permission systems for Authority;
- target resolvers and sandboxes/mediated APIs for Scope;
- metered tool adapters for Cost;
- subprocess cancellation, task cancellation, or service deadlines for Duration;
- filesystem/API/service observers for Telemetry;
- validators and environment queries for ordinary Requirements;
- MCP transport, authorization, schemas, and tool errors for MCP Techniques.

When the environment cannot expose the mechanism, the Kernel refuses closure rather than downgrading the Requirement to prose.

## CAST 0.4

CAST remains the single execution receipt. 0.4 adds required Technique provenance so later evidence can distinguish implementation behavior from Spell semantics.

The record includes:

- Spell name/version;
- Effect;
- Caster;
- target;
- Technique Binding id/version/kind;
- optional Familiar;
- closure decision/reasons;
- observations tied to Requirement ids;
- outcome;
- residuals;
- execution result where available.

This forbids aggregating reliability across different Techniques while losing which implementation actually ran.

## Familiar

Familiar remains optional and advisory. Changing Familiar may alter guidance representation or attention. It may not alter:

- selected Spell/Effect;
- Technique Binding compatibility;
- Authority;
- Scope;
- Cost;
- Duration;
- Requirement satisfaction;
- outcome classification.

This forbids a dialect/judgment layer from becoming an execution authority.

## Current executable evidence

The 0.4 validation layer currently demonstrates:

- exact Spell/version/Effect binding matching;
- refusal before executor invocation when binding Duration support is absent;
- refusal before executor invocation when binding Scope support is absent;
- Technique identity retained in CAST;
- two different Technique Bindings producing equivalent Requirement-level Spell behavior without modifying the Spell declaration.

The test suite also carries an expected-failure fixture showing that a binding's Scope-support claim alone cannot prevent an unrestricted Technique from mutating data outside the resolved Scope. This is intentional evidence of the remaining environmental-containment gap.

## 0.4 release blockers

0.4 is not complete until:

1. a reference consequence path enforces Scope against an attempted out-of-scope operation rather than merely relying on Technique cooperation;
2. Authority is similarly tied to the credentials/capabilities used by the effectful path;
3. the real `workspace-tidy` Effect is migrated through the 0.4 binding path;
4. a second implementation realizes the same real Effect without changing `SPELL.md`;
5. at least one MCP-backed Technique passes the same closure/CAST rules;
6. the expected-failure Scope containment test becomes an ordinary passing test because the runtime/environment actually blocks the operation;
7. binding capability claims have conformance fixtures appropriate to each supported implementation kind.

## Deferred

0.4 does not need to solve:

- standing/level/grade;
- Stats/Scaling aggregation;
- durable Spell State;
- generalized Domain metadata;
- universal Scope expressions beyond tested mechanisms;
- arbitrary Cost unit registries;
- multiple Familiars.

Those should remain downstream of trustworthy casting and Technique portability.
