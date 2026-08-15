---
name: spellcraft
description: Author, inspect, repair, and migrate Agent Spells SPELL.md declarations. Use when turning an existing Skill or MCP-backed capability into a portable effect declaration, separating Spell properties from caster preferences, Technique requirements, and runtime observations, writing effect checks, or revising a declaration from CAST records. Spellcraft is an Agent Skill, not a Spell, and it is not present at cast time.
---

# Spellcraft

Spellcraft studies a capability and writes the smallest portable declaration whose effects a runtime can actually gate and investigate.

It may work with no Agent Spells Kernel. A Familiar, Owl, library, another caster, or another Spell may assist, but none is required. When a Spell is used during Spellcraft, that use is a separate cast.

## Start from the core shape

Before writing `SPELL.md`, sort the capability through these concerns:

- **Domain** — where the effect has meaning. Keep it only when a host can resolve whether the target is in that domain.
- **Description** — discovery/inspection text. It is author-asserted and never proof.
- **Effect** — the runtime change or resulting condition being attempted. This is the center of the Spell.
- **Scope** — what the effect may reach and how much. A runtime must be able to resolve the requested scope and enforce the declared boundary.
- **Requirements** — conditions that gate execution before it starts and conditions that must hold afterward for the effect to count.
- **Telemetry** — current observations needed to resolve Domain, Scope, or Requirements. Freshness matters when stale state could change the decision.
- **Cost** — measurable resources whose bounds matter to whether or how the effect may run. SPELL declares bounds; CAST records actual cost.
- **Duration** — measurable time bounds that matter to execution, observation, or effect lifetime. SPELL declares bounds; CAST records actual timing.

Do not treat every concern as a required field. A Spell that has no meaningful cost or duration boundary should not invent one.

## Keep these outside the Spell declaration

- **Instructions** belong to a Skill, Technique, tool, service, or host binding. Two Techniques should be able to realize the same Spell effect without changing the declaration.
- **State** belongs to runtime/CAST unless a required starting or resulting state is expressed as Telemetry or a Requirement.
- **Stats** are derived from CAST records. They are not author claims.
- **Scaling** is learned from Stats and repeated casts. If scaling evidence later justifies a hard bound, express that bound through Scope, Cost, Duration, or Requirements in a new declaration version.

## Field survival test

A portable field survives only if at least one is true:

1. it helps a host select or inspect the Spell (`description` is the deliberate author-asserted case);
2. it can gate whether an effect may execute;
3. it constrains effectful execution in a way a host can check;
4. it determines whether the effect occurred.

If none apply, remove the field from the portable declaration.

For every retained mechanism, state what it forbids. Examples:

- Domain resolution forbids casting against a target whose declared domain cannot be confirmed.
- Scope resolution forbids an implementation from silently reaching beyond the resolved target.
- Requirement checking forbids an executor from treating its own success report as proof of an independent postcondition.
- Cost accounting forbids actual resource use from being replaced by an author's estimate in CAST.
- Duration accounting forbids indefinite execution or observation when the declaration sets a finite bound.
- Familiar guidance forbids dialect or preference from widening Scope, authority, or changing the Effect.

## Effect ownership

Prefer effect-local constraints. Different effects in one Spell may require different telemetry, authority, scope, cost, duration, and postconditions.

The Spell identifies the portable capability. The selected Effect is what the caster actually asks the runtime to attempt.

## Requirements are the validation spine

For each Requirement, be able to answer:

- Is it evaluated before or after execution?
- What host observation/checker can resolve it?
- What counts as satisfied?
- What does the runtime do if it is missing, denied, violated, or unavailable?

A before Requirement gates closure. An after Requirement determines effect confirmation and becomes a residual when it remains unresolved.

Authority is a before Requirement resolved by the host/security environment. Familiar, caster prose, Skill instructions, or executor output cannot self-certify authority.

## Cost and Duration

Keep only measurable, consequential bounds.

Useful Cost examples include tool calls, bytes written, files changed, compute, monetary spend, quota, or required approvals when the host can account for them.

Duration can constrain execution time, the observation window used to confirm an effect, or the lifetime of a temporary effect. Actual timestamps and elapsed values belong in CAST.

Do not encode adjectives such as `high concentration` or `medium effort` as protocol values unless the host has a real measurement/gating mechanism for them.

## Familiar and Owl

A Familiar is caster-authored dialect and judgment configuration, not Spell semantics. A valid Familiar may change guidance representation and attention while leaving Effect, Scope, Requirements, Cost, Duration, authority, execution, and outcome unchanged.

Owl may review a candidate by asking:

- Is there an observable Effect, or only instructions?
- Which fields actually gate or confirm it?
- Did a caster preference leak into the Spell?
- Did one Technique's dependency leak into the Spell?
- Are Scope, Cost, or Duration claims measurable?
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
- declared Cost -> actual measured cost;
- declared Duration -> actual timing;
- unresolved after Requirements -> residuals.

Change `SPELL.md` only when runtime evidence shows the declaration is missing or misstating a real condition. Do not improve apparent capability by changing description text.

## Current format boundary

`../format/SPECIFICATION.md` 0.2 remains the normative portable format until a tested 0.3 revision is adopted. Domain, Scope, Cost, and Duration are currently under structural validation; do not invent incompatible frontmatter merely because Spellcraft has identified them as likely core concerns.

The next format revision should be driven by fixtures that demonstrate their gating and observation behavior.

## Spellcraft forbids

- declaring level, grade, standing, or derived category from author judgment;
- treating Skill/MCP/executor success as proof of a declared effect;
- encoding one caster's Familiar preferences as universal Spell requirements;
- encoding one Technique's dependencies as Spell properties unless every valid Technique requires them;
- putting runtime State or derived Stats into `SPELL.md`;
- asserting Scaling where no CAST evidence supports it;
- adding a portable field that neither gates, constrains, confirms, selects, nor materially improves inspection of an effect.
