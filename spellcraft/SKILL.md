---
name: spellcraft
description: Author, inspect, repair, and migrate Agent Spells SPELL.md declarations. Use when turning an existing Skill or MCP-backed capability into a portable effect declaration, separating Spell properties from caster preferences, Technique requirements, and runtime observations, writing effect checks, or revising a declaration from CAST records. Spellcraft is an Agent Skill, not a Spell, and it is not present at cast time.
---

# Spellcraft

Spellcraft studies a capability and writes the smallest portable declaration whose effects a runtime can actually gate and investigate.

It may work with no Agent Spells Kernel. A Familiar, Owl, library, another caster, or another Spell may assist, but none is required. When a Spell is used during Spellcraft, that use is a separate cast.

## Start from the core shape

Before writing `SPELL.md`, sort the capability through these concerns:

- **Domain** — where the effect has meaning. Keep it only when a host can resolve whether the target is in that domain or when it materially improves discovery.
- **Description** — discovery/inspection text. It is author-asserted and never proof.
- **Effect** — the runtime change or resulting condition being attempted. This is the center of the Spell.
- **Scope** — what the effect may reach and how much. Keep it only when the runtime can persist the resolved target/scope and enforce a portable bound.
- **Requirements** — conditions that gate execution before it starts and conditions that must hold afterward for the effect to count.
- **Telemetry** — current observations needed to resolve Domain, Scope, or Requirements. Freshness matters when stale state could change the decision.
- **Cost** — measurable resources whose bounds matter to whether or how the effect may run. Keep it only when the relevant runtime/Technique path can meter and deny the next unit before crossing the ceiling.
- **Duration** — measurable time bounds that matter to execution, observation, or effect lifetime. Keep it only when the relevant runtime/Technique path can enforce the time boundary rather than merely observe it afterward.

Do not treat every concern as a required field. A Spell that has no meaningful Cost or Duration boundary should not invent one.

## Keep these outside the Spell declaration

- **Instructions** belong to a Skill, Technique, tool, service, or host binding. Two Techniques should be able to realize the same Spell effect without changing the declaration.
- **State** belongs to runtime/CAST unless a required starting or resulting state is expressed as Telemetry or a Requirement.
- **Stats** are derived from CAST records. They are not author claims.
- **Scaling** is learned from Stats and repeated casts. If scaling evidence later justifies a hard bound, express that bound through Scope, Cost, Duration, or Requirements in a new declaration version.
- **Generic Limit** should not be added to new candidate structure as a catch-all. Current FORMAT 0.2 still supports `limits` for compatibility, but the validated candidate shape gives reach to Scope, resources to Cost, time to Duration, and invariants to Requirements.

## Field survival test

A portable field survives only if at least one is true:

1. it helps a host select or inspect the Spell (`description` is the deliberate author-asserted case);
2. it can gate whether an effect may execute;
3. it constrains effectful execution in a way a host can check;
4. it determines whether the effect occurred.

If none apply, remove the field from the portable declaration.

For every retained mechanism, state what it forbids. Examples:

- Domain resolution forbids casting against a target whose declared domain cannot be confirmed when Domain is used as a gate.
- Scope resolution forbids an implementation from silently reaching beyond the resolved target.
- Requirement checking forbids an executor from treating its own success report as proof of an independent postcondition.
- Cost accounting forbids a compliant binding from consuming another metered unit after the declared ceiling would be exceeded.
- Duration accounting forbids a compliant binding from continuing past a finite execution boundary and later calling the cast resolved merely because it eventually returned.
- Familiar guidance forbids dialect or preference from widening Scope, authority, or changing the Effect.

## Effect ownership

Prefer effect-local constraints. Different effects in one Spell may require different telemetry, authority, Scope, Cost, Duration, and postconditions.

The Spell identifies the portable capability. The selected Effect is what the caster actually asks the runtime to attempt.

## Requirements are the validation spine

For each Requirement, be able to answer:

- Is it evaluated before or after execution?
- What host observation/checker can resolve it?
- What counts as satisfied?
- What does the runtime do if it is missing, denied, violated, or unavailable?

A before Requirement gates closure. An after Requirement determines effect confirmation and becomes a residual when it remains unresolved.

Authority is a before Requirement resolved by the host/security environment. Familiar, caster prose, Skill instructions, or executor output cannot self-certify authority.

Prefer Requirements over generic Limit when the claimed boundary is actually an observable invariant. The external `workspace-tidy` fixture now proves this: preserving unmarked files is an after Requirement checked from pre/post file digests, not a generic Limit, and the external guarantee is unchanged.

## Cost and Duration

Keep only measurable, consequential bounds.

The reference Kernel has now demonstrated two useful mechanisms:

- a Duration bound can be handed to a Technique binding that actually terminates over-duration subprocess execution;
- a Cost ceiling can be handed to a Technique binding that rejects the next metered unit before the next action occurs.

Those mechanisms do not yet make Cost or Duration portable FORMAT fields. The declaration path, portable units/resource names, observation windows, and temporary effect lifetime still need validation.

Useful Cost examples include tool calls, bytes written, files changed, compute, monetary spend, quota, or required approvals when the host can account for them.

Duration can constrain execution time, the observation window used to confirm an effect, or the lifetime of a temporary effect. Actual timestamps and elapsed values belong in CAST only when timing is material to the cast.

Do not encode adjectives such as `high concentration` or `medium effort` as protocol values unless the host has a real measurement/gating mechanism for them.

## Scope is not just a target name

A host knowing what object it intends to touch does not prove portable Scope semantics.

Before promoting Scope into FORMAT, require both:

- the declaration contains a machine-readable boundary that another host can inspect;
- CAST retains the concrete target/resolved Scope so later readers can tell what the bound applied to.

The current Kernel accepts a target but CAST 0.2 does not retain it, so Scope is still structurally justified but not yet validated as a portable field.

## Familiar and Owl

A Familiar is caster-authored dialect and judgment configuration, not Spell semantics. A valid Familiar may change guidance representation and attention while leaving Effect, Scope, Requirements, Cost, Duration, authority, execution, and outcome unchanged.

Owl may review a candidate by asking:

- Is there an observable Effect, or only instructions?
- Which fields actually gate or confirm it?
- Did a caster preference leak into the Spell?
- Did one Technique's dependency leak into the Spell?
- Are Scope, Cost, or Duration claims measurable and enforceable?
- Is a generic Limit hiding a more precise Scope, Cost, Duration, or Requirement?
- Is Scaling being asserted before CAST evidence exists?
- Is live State being mistaken for declaration data?

Owl advises; FORMAT and runtime evidence decide what survives.

## Use CAST to redraw

Read CAST as the runtime counterpart to the declaration:

- declared Domain -> resolved environment;
- declared Effect -> attempted effect and observed result;
- declared Scope -> resolved target/reach;
- declared Telemetry -> observations actually obtained;
- declared Requirements -> before/after results;
- declared Cost -> actual metered cost when a real meter participates;
- declared Duration -> actual bound/timing when Duration participates;
- unresolved after Requirements -> residuals.

Change `SPELL.md` only when runtime evidence shows the declaration is missing or misstating a real condition. Do not improve apparent capability by changing description text.

## Current format boundary

`../format/SPECIFICATION.md` 0.2 remains the normative portable format until a tested 0.3 revision is adopted. Domain, Scope, Cost, and Duration are candidate concerns under structural validation; do not invent incompatible frontmatter merely because Spellcraft has identified them as likely useful.

Generic `limits` remains part of FORMAT 0.2 for compatibility, but current evidence argues against carrying it forward unless a future fixture finds a unique job that Scope, Cost, Duration, or Requirements cannot perform.

The next format revision should be driven by fixtures that demonstrate gating and observation behavior, not vocabulary preference.

## Spellcraft forbids

- declaring level, grade, standing, or derived category from author judgment;
- treating Skill/MCP/executor success as proof of a declared effect;
- encoding one caster's Familiar preferences as universal Spell requirements;
- encoding one Technique's dependencies as Spell properties unless every valid Technique requires them;
- putting runtime State or derived Stats into `SPELL.md`;
- asserting Scaling where no CAST evidence supports it;
- using generic Limit as a dumping ground for a boundary with a more precise owner;
- adding a portable field that neither gates, constrains, confirms, selects, nor materially improves inspection of an effect.
