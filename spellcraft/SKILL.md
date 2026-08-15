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

Scope, Cost, Duration, Authority, target compatibility, preservation rules, and postconditions are currently treated as forms of Requirements rather than peer Spell fields.

FORMAT 0.2 remains the compatibility baseline. `../format/0.3-draft/` records the requirement-centered draft that current fixtures support.

## Requirements are the validation spine

A Requirement has a stable id and a phase. CAST must preserve that id so the declaration can be compared directly to runtime evidence.

### Before

Before Requirements decide whether execution may begin.

Validated forms include:

- ordinary host-checkable conditions;
- **Authority** resolved by the host/security environment;
- **Scope** resolved against a concrete target and machine-readable bound.

A before Requirement forbids effectful execution when the condition is unavailable, denied, violated, or otherwise unsatisfied.

### During

During Requirements govern effectful execution while it is occurring.

Validated forms include:

- **Cost** — a metered resource ceiling that rejects the next unit before the ceiling is crossed;
- **Duration** — a finite execution bound that a participating Technique/runtime path can actually contain.

Do not call after-the-fact measurement enforcement. If the Technique cannot participate in the meter or timeout, the runtime cannot honestly claim the Requirement is governed.

### After

After Requirements determine whether the Effect can count as resolved.

They are checked from post-execution observations, independently of the Technique's own success report. An unresolved after Requirement becomes a residual.

The real `workspace-tidy` fixture demonstrates this twice: disposable files must be absent, and every unmarked pre-existing file must remain byte-identical.

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

The Kernel 0.3 draft adds an important open requirement: closure must know whether the selected Technique can truly support the declared during mechanisms. Merely passing a timeout or cost object is not proof that the Technique honors it.

## Familiar and Owl

A Familiar is caster-authored dialect and judgment configuration, not Spell semantics. It may change guidance representation and attention, but not Effect, Requirements, Authority, Scope, Cost, Duration, execution behavior, or outcome.

Owl reviews the craft by asking:

- Is there an observable Effect or only instructions?
- Which Requirements actually gate, govern, or confirm it?
- Is a caster preference leaking into the declaration?
- Is a Technique dependency pretending to be a Spell Requirement?
- Can Scope, Cost, and Duration actually be enforced?
- Is a generic Limit hiding a more precise Requirement?
- Is live State or derived Scaling being presented as declaration truth?
- Can CAST point back to the exact Requirement ids that mattered?

Owl advises. FORMAT validation and runtime evidence decide what survives.

## Use CAST to redraw

Read CAST as the runtime counterpart to the declaration:

- selected Effect -> attempted Effect and outcome;
- Telemetry -> observations actually obtained;
- before Requirements -> closure evidence;
- during Requirements -> execution-governance evidence;
- after Requirements -> effect-confirmation evidence;
- target -> concrete object/reach the Effect applied to;
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
- different Familiar dialects with unchanged Spell behavior.

These are mechanics results, not Spell standing.

## Spellcraft forbids

- declaring level, grade, standing, or reliability from author judgment;
- treating Skill/MCP/executor success as proof of an Effect;
- encoding Familiar preferences as universal Requirements;
- encoding one Technique's dependencies as Spell properties unless every valid Technique requires them;
- putting live State, Stats, or asserted Scaling into `SPELL.md`;
- using generic Limit as a dumping ground;
- claiming Cost or Duration enforcement when the bound Technique cannot actually participate;
- adding structure that neither selects, gates, governs, confirms, nor materially improves inspection of an Effect.
