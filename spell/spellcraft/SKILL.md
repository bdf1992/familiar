---
name: spellcraft
description: Author, inspect, repair, and migrate Agent Spells SPELL.md declarations. Use when turning an existing Skill or MCP-backed capability into a portable effect declaration, separating Spell properties from caster preferences, Technique requirements, and runtime observations, writing effect requirements, or revising a declaration from CAST records. Spellcraft is an Agent Skill, not a Spell, and it is not present at cast time.
---

# Spellcraft

Spellcraft studies a capability and writes the smallest portable declaration whose Effects a runtime can actually gate and investigate.

It may work with no Agent Spells Kernel. A Familiar, Owl, library, another caster, or another Spell may assist, but none is required. When a Spell is used during Spellcraft, that use is a separate cast.

## Start with the Effect

Ask what runtime change or resulting condition is actually being attempted. If the answer is only instructions, expertise, or a procedure, keep the work as a Skill or Technique.

A Spell declaration needs an Effect that can be investigated independently of executor confidence.

## Current core shape

The validated 0.3 draft is smaller than the original field list:

- **Description** — author-asserted discovery/inspection text;
- **Telemetry** — current observations needed by the Effect;
- **Effect** — the attempted runtime change/result;
- **Requirements** — the conditions under which that Effect may begin, continue, and count as resolved.

Identity/version metadata remains required by the FORMAT.

Scope, Cost, Duration, Authority, target compatibility, preservation rules, and postconditions are treated as forms of Requirements rather than peer Spell fields.

FORMAT 0.2 remains the compatibility baseline. `../format/0.3-draft/` records the requirement-centered draft. `../../cast/kernel/0.4-draft/` records the current casting/binding validation work. `../../environment/MAGIC.md` records the 0.6 candidate runtime semantics for conserved Mana and maintenance participation.

## Craft against one casting law

Every Spell is cast through the same runtime order. Spellcraft changes which Requirements exist, not the order in which runtime truth is established.

The Kernel resolves the invocation, validates the Spell/Caster/optional Familiar/Technique Binding, builds the Requirement plan, verifies that required environment and Technique mechanisms exist, resolves target and Telemetry, evaluates before Requirements, closes or refuses, governs effectful execution, observes afterward, evaluates after Requirements, then emits CAST.

Spellcraft must therefore ask of every Requirement:

- when must it be known or enforced?
- what concrete runtime/environment mechanism answers or enforces it?
- can effectful execution bypass the checked boundary?
- what observation will appear in CAST?

If there is no concrete answer, the Requirement is currently prose rather than enforceable protocol.

## Requirements are the validation spine

A Requirement has a stable id and a phase. CAST must preserve that id so the declaration can be compared directly to runtime evidence.

### Before

Before Requirements decide whether execution may begin.

Validated forms include:

- ordinary host-checkable conditions;
- **Authority** resolved by the host/security environment;
- **Scope** resolved against a concrete target and machine-readable bound.

A before Requirement forbids effectful execution when the condition is unavailable, denied, violated, or otherwise unsatisfied.

A before check is not automatically a complete consequence boundary. Authority and Scope also require the eventual effectful path to remain inside the authority/scope that was resolved before closure.

### During

During Requirements govern effectful execution while it is occurring.

Validated forms include:

- **Cost** — a metered resource ceiling that rejects the next unit before the ceiling is crossed;
- **Duration** — a finite execution bound that a participating Technique/runtime path can actually contain.

Do not call after-the-fact measurement enforcement. If the Technique cannot participate in the meter or containment path, the runtime cannot honestly claim the Requirement is governed.

Material/component use may naturally have two Requirements: availability before closure and consumption during execution. Do not consume a component merely because an invocation was attempted when the Spell says payment occurs later.

### After

After Requirements determine whether the Effect can count as resolved.

They are checked from post-execution observations, independently of the Technique's own success report. An unresolved after Requirement becomes a residual.

The real `workspace-tidy` fixture demonstrates this twice: disposable files must be absent, and every unmarked pre-existing file must remain byte-identical.

## Consequence-boundary test

A Requirement that constrains consequences must survive this question:

> Can the selected Technique/environment still produce the forbidden consequence after the preflight check passed?

If yes, the current implementation does not fully enforce the Requirement.

Examples:

- counting a resolved Scope before execution does not enforce Scope if arbitrary Technique code can later touch other targets;
- checking Caster Authority does not enforce Authority if execution runs with broader credentials;
- counting Cost after execution does not enforce a Cost ceiling;
- measuring elapsed Duration after an uncontainable executor returns does not enforce Duration.

The 0.4 casting work intentionally retains a failing Scope-containment conformance case until a real environment control blocks the out-of-Scope operation.

## Runtime-derived properties

Some properties affect a Cast while remaining situated runtime truth rather than portable Spell declaration truth.

Current examples include:

- participation role;
- Mana disposition, reach, and availability;
- current runtime limits;
- maintenance admission and restoration;
- runtime level admission or standing where later evidence establishes it.

Spellcraft may discover that an Effect depends on one of these mechanisms. It must not copy the current value into `SPELL.md` merely because the runtime exposes it.

For Mana-bearing work, ask which runtime transition is actually required: claim, commit, spend, release, drain, or restoration. Mana conservation, claims, and runtime ceilings are Environment facts unless later evidence proves a portable Spell Requirement is needed.

The 0.6 candidate deliberately does not yet define Level 0 or a portable Spell level field.

## Maintenance effects

Maintenance is an Effect on a concrete mechanism, not prose about a mechanism.

A candidate maintenance Effect should identify:

- the domain and concrete mechanism being maintained;
- the observable before condition;
- the attempted change;
- an independent after observation;
- the runtime boundary that prevents replay or self-certification.

`Domains Maintainer` is a situated role, not evidence that maintenance happened. A Skill or Cast may supply one Maintenance Act, but the runtime independently decides whether it was confirmed and whether any existing Spent Mana became restorable.

Do not describe restoration as creating, minting, awarding, or paying Mana. Verified restoration returns existing Spent Mana to Ambient. Claiming that Mana is a later ordinary runtime operation.

A repeated Maintenance Act must not produce repeated runtime consequence.

## What the validation removed

### Generic Limit

Do not add a generic Limit to new candidate structure merely because a constraint exists. Current evidence gives the constraint to the more precise owner:

- reach/quantity -> Scope Requirement;
- resource ceiling -> Cost Requirement;
- execution time -> Duration Requirement;
- safety/preservation/result-state -> ordinary Requirement.

FORMAT 0.2 retains `limits` only for compatibility. The 0.3 draft removes it.

### Domain as runtime semantics

The Domain fixture showed that target compatibility is fully enforceable as a before Requirement. Domain therefore has no demonstrated unique runtime job. If catalogs later need Domain as discovery metadata, evaluate that separately from casting semantics.

This does not conflict with `Domains Maintainer`: there, `domain` identifies which existing repository subject domain owns the concrete mechanism being maintained; it does not determine Spell target compatibility.

### Instructions

Instructions remain in Skills, Techniques, MCP bindings, scripts, or services. Replacing the Technique should not require rewriting the Spell declaration.

### State

Live state belongs to runtime/CAST. State that affects validity is observed through Telemetry and tested through Requirements. Do not add durable Spell State until a concrete cross-cast Effect proves it is necessary.

### Stats and Scaling

Stats come from CAST records. Scaling is learned from repeated casts. Neither is author-declared Spell truth.

## Field survival test

A portable field or structure survives only if at least one is true:

1. it materially helps selection or inspection;
2. it gates whether an Effect may execute;
3. it constrains execution through a host-checkable mechanism;
4. it determines whether the Effect occurred.

If none apply, remove it.

For every mechanism, state what it forbids.

## Technique separation

A Technique is implementation material used to attempt an Effect.

Spellcraft should ask:

- Can another Skill/MCP tool/service realize the same Effect without changing the declaration?
- Does a proposed Requirement belong to every valid Technique, or only the current implementation?
- Can the runtime actually observe or enforce what the declaration claims?
- Can the selected Technique participate in every required effect-path control?

The 0.4 Technique Binding draft records the exact Spell/version/Effect realized plus Authority, Scope, Cost, and Duration mechanisms the execution path claims to support. Closure refuses when required support is absent.

A schema-valid binding is still an assertion about implementation behavior. Conformance tests and, where needed, hard environment isolation are what turn that assertion into evidence.

## Familiar and Owl

A Familiar is caster-authored dialect and judgment configuration, not Spell semantics. It may change guidance representation and attention, but not Effect, Requirements, Authority, Scope, Cost, Duration, Technique compatibility, execution behavior, or outcome.

Owl reviews the craft by asking:

- Is there an observable Effect or only instructions?
- Which Requirements actually gate, govern, or confirm it?
- Is a caster preference leaking into the declaration?
- Is a Technique dependency pretending to be a Spell Requirement?
- Can Scope, Authority, Cost, and Duration actually be enforced through the consequence path?
- Is a generic Limit hiding a more precise Requirement?
- Is live State or derived Scaling being presented as declaration truth?
- Can CAST point back to the exact Requirement ids and Technique that mattered?
- Is a runtime-derived Mana, role, capacity, maintenance, or level fact being mistaken for portable Spell truth?
- If this is maintenance, what concrete mechanism changed and who independently observed it?

Owl advises. FORMAT validation and runtime evidence decide what survives.

## Use CAST to redraw

Read CAST as the runtime counterpart to the declaration:

- selected Effect -> attempted Effect and outcome;
- Telemetry -> observations actually obtained;
- before Requirements -> closure evidence;
- during Requirements -> execution-governance evidence;
- after Requirements -> effect-confirmation evidence;
- target -> concrete object/reach the Effect applied to;
- Technique -> implementation that actually attempted the Effect;
- unresolved conditions -> residuals.

Change `SPELL.md` only when runtime evidence shows that the declaration is missing or misstating a real condition. Do not improve apparent capability by changing description text.

## Current evidence

The reference suite now demonstrates:

- independent external effect observation;
- Authority refusal;
- Scope refusal before Technique execution;
- Cost refusal before excess consumption;
- Duration containment;
- post-observation after executor failure;
- preservation as an after Requirement rather than generic Limit;
- target compatibility as a before Requirement rather than Domain runtime semantics;
- exact Requirement ids retained into the 0.3 candidate CAST;
- machine Caster records;
- different Familiar dialects with unchanged Spell behavior;
- exact Technique Binding matching;
- closure refusal when a binding lacks Scope or Duration support;
- Technique identity in 0.4 CAST;
- two different synthetic Techniques producing equivalent Spell-level Requirement results without changing the Spell declaration;
- conserved Mana across claim, flow, commitment, settlement, drain, restoration, and restart;
- runtime-resolved access before sensing, claiming, releasing, or committing;
- one-use maintenance evidence with independent structured verification;
- Spent Mana provenance retained to the Cast that produced it;
- maintained Magic settings that cannot change `total_mana` or invalidate live state.

These are mechanics results, not Spell standing.

## Spellcraft forbids

- declaring level, grade, standing, or reliability from author judgment;
- treating Skill/MCP/executor success as proof of an Effect;
- encoding Familiar preferences as universal Requirements;
- encoding one Technique's dependencies as Spell properties unless every valid Technique requires them;
- putting live State, Stats, asserted Scaling, current Mana, current role, or runtime limits into `SPELL.md` as declaration truth;
- treating maintenance prose, role identity, or executor self-report as a Maintenance Act;
- describing Mana restoration as creation or direct payment to a Maintainer;
- using generic Limit as a dumping ground;
- claiming Scope or Authority enforcement from preflight alone when the consequence path can bypass it;
- claiming Cost or Duration enforcement when the bound Technique cannot actually participate;
- treating a Technique Binding capability claim as proof without conformance/environment evidence;
- adding structure that neither selects, gates, governs, confirms, nor materially improves inspection of an Effect.
