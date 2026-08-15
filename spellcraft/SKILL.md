---
name: spellcraft
description: "Study, design, structure, test, migrate, and improve Spell candidates. Use when creating a new Spell candidate, upgrading a Skill or Trick toward Spell behavior, analyzing cast receipts or residuals, designing Trials, separating Spell properties from caster preferences or implementation details, or repairing a candidate after fizzles or wild magic. Spellcraft is a Skill, not a Spell: it may be used with no Spell Runtime at all, and it may optionally use Familiars, libraries, tools, other casters, and independently cast Spells as evidence or assistance. Never assign demonstrated Spell standing from design intent; runtime impacts, evidence, residuals, and Trials determine whether a candidate is a Trick or Spell."
---

# Spellcraft

Spellcraft studies an ability and produces the smallest castable Spell candidate worth testing. It improves candidates from observed casts rather than improving their apparent standing by description.

> Craft from effects backward. Learn from casts forward.

Spellcraft is a **Skill**. It does not cast Spells, require a Spell Runtime, or declare that a candidate is a demonstrated Spell. When Spellcraft uses a Familiar or another Spell, that assistance is a separate cast governed by its own runtime contract and receipt.

## Keep these distinctions sharp

- **Skill:** reusable competence or procedure.
- **Trick:** bounded recognizable effect without demonstrated Spell governance.
- **Spell candidate:** crafted portable definition that can be offered to a Spell Runtime.
- **Spell:** runtime-demonstrated capability whose valid effects are governed by relevant telemetry, requirements, limits, energy, evidence, and residuals.
- **Technique:** a known way to realize part or all of a Spell's ability; an existing Skill may become a Technique rather than the Spell itself.
- **Cast:** one runtime application of a Spell candidate or demonstrated Spell.

A Spell candidate is an artifact of Spellcraft. A Spell is a classification earned from casting evidence.

## Gather only useful materials

Use whatever is available and authorized; none is mandatory except enough subject matter to craft honestly:

- the crafter's intent and domain knowledge;
- existing Skills, scripts, tools, MCP capabilities, or Techniques;
- a Familiar, when the caster wants its help;
- a library or pattern commons of candidates, Tricks, Spells, Trials, receipts, and lessons;
- prior cast receipts, impacts, fizzles, disturbances, wild magic, and residuals;
- another caster or reviewer who can expose hidden assumptions;
- direct investigation of the environment when runtime behavior is unclear.

A no-runtime environment can still produce a valid **candidate** and Trial plan. State its standing as untested rather than inventing runtime evidence.

## Work the craft

### Study

Identify the inherent ability before naming a bag of effects. Ask what all proposed Expressions have in common and what existing competence already works.

Study examples and failures. Prefer real effects, receipts, and observed constraints over fantasy wording.

### Distinguish

Separate:

- properties of the Spell from preferences of its first caster;
- Spell requirements from requirements of one implementation;
- live telemetry from user input, inference, and assumption;
- inherent ability from individual Tricks or Techniques;
- expected effects from evidence that an effect actually occurred;
- residuals from disturbances and wild magic.

A Familiar may strongly influence the caster's preferred expression without becoming a universal law of the Spell.

### Craft

Produce the smallest coherent candidate that specifies:

- stable identity and inherent ability;
- known Expressions and optional magic words;
- telemetry that must be observed;
- requirements that must hold;
- limits that may not be crossed;
- energy/resources that materially affect the cast;
- expected effect class;
- evidence appropriate to claimed effects;
- explicit handling for partial effects, fizzles, disturbances, wild magic, and residuals;
- falsifying Trials.

Do not inflate the candidate with concepts that belong only to one implementation or one Familiar.

### Prepare

Identify Techniques that could realize the candidate. Reuse existing Skills and MCP tools instead of rewriting working competence.

Prepare contrastive Trials where relevant conditions differ. At minimum, test the boundaries the candidate claims to govern.

Every candidate intended to interoperate with Familiars should include a **foreign Familiar Trial**: at least one valid Familiar other than the one used during authoring must be able to assist without changing the Spell's inherent ability, widening authority, fabricating telemetry, or waiving limits.

### Cast

If a Spell Runtime is available, use it for Trial casts. Casting is outside Spellcraft itself.

Treat every assisting Spell as a separate cast. For example, `Summon Familiar` during Spellcraft may produce advice that becomes craft material, but that Familiar cast retains its own contract and receipt.

### Read

After a cast, inspect the complete runtime story:

```text
before state / telemetry
        -> casting decision
        -> actions
        -> runtime impact
        -> evidence
        -> residuals
        -> disturbances / wild magic
```

Do not rationalize surprising impacts into the expected effect after the fact.

### Redraw

Use Marks from receipts and Trials to revise the candidate, Techniques, requirements, limits, evidence model, or Trial set.

Choose the right repair path:

- use **Spellcraft** when the candidate itself appears malformed;
- use the **Familiar** when caster expression, stake, interpretation, or preferred technique is the issue;
- use **another Casting** when the Spell is sound and a separate bounded effect remains;
- use **another Caster** when independent expertise, authority, or reproduction matters;
- investigate the **environment** when causality of a disturbance is unresolved.

### Release honestly

Leave the work in the strongest state the evidence earns:

- untested Spell candidate;
- Novice / Practiced / Master Trick;
- demonstrated Spell with runtime-assigned Level and Grade.

A Master Trick can be a successful outcome. Do not add telemetry theater merely to force it over the Level 0 line.

## Familiar-assisted Spellcraft

A Familiar can help the crafter notice non-obvious Expressions, choose proportionate energy, identify meaningful limits, expose caster-specific preferences, and interpret residuals. The Owl is especially useful for completion, continuity, malformed metaphors, and detecting spell-shaped documentation that has not become an effect.

Familiars advise from their form and stake. They cannot manufacture authority, telemetry, evidence, or runtime standing.

Spellcraft MUST remain usable without a Familiar.

## Failure vocabulary

Use these terms precisely when reading casts:

- **Fizzle:** the casting cannot validly resolve its intended effect because a required part of the casting contract is absent, invalid, incompatible, or breaks during execution.
- **Residual:** intended effect that remains unresolved, unverified, or intentionally untouched.
- **Disturbance:** unexpected environmental observation whose causal relation to the cast is not yet established.
- **Wild magic:** a materially unexpected effect attributable or strongly linked to the casting and outside the expected effect model.

A fizzle does not prove that nothing happened. Preserve and investigate unexpected impacts.

## Quality test

A Spellcraft pass is good when it makes the candidate easier to falsify, cast, inspect, and improve.

Before finishing, check:

- Is there one coherent inherent ability?
- Can the candidate be cast by a compatible runtime without relying on hidden author context?
- Would relevant telemetry actually change valid casting behavior?
- Are requirements and limits distinct and enforceable?
- Are Spell properties separated from Familiar/caster preferences and implementation details?
- Can any valid structured Familiar assist without corrupting the cast?
- Can an effect be distinguished from its residuals and unexpected impacts?
- Do the Trials have a realistic chance to prove the candidate is only a Trick?

If not, keep crafting rather than declaring magic.
