# Familiar

**Familiar** is an experimental Spell system growing out of Draw the Owl.

The Owl helps a caster form a Familiar. A Familiar helps a caster cast Spells. A Spell turns an expressive intention into a grounded effect under live telemetry, requirements, limits, energy, and evidence.

> Magic may be expressive. Effects must be accountable.

## What is a Spell?

A **Skill** packages reusable competence and instructions.

A **Trick** produces a bounded recognizable effect but has not yet demonstrated the runtime governance required of a Spell.

A **Spell** is a telemetry-aware, contract-governed expressive capability whose valid casting depends on present reality. Spells are demonstrated, not declared.

A Spell has:

- an **inherent ability** — the stable capability all of its expressions share;
- **magic words** — compact human-facing invocations, never mandatory syntax;
- **telemetry** — state that must be observed rather than assumed;
- **requirements** — conditions that must hold;
- **limits** — boundaries a cast may not cross;
- **energy** — resources available and committed to the cast;
- an **effect** — the actual consequence of casting;
- **evidence** — proof appropriate to the claimed effect;
- **trials** — scenarios that demonstrate how the Spell behaves when reality changes.

The Spell runtime validates these contracts, resolves casts, records receipts, and evaluates demonstrated standing.

## Standing, level, and grade

Spellcraft is graded rather than binary.

- **Novice Trick** — useful spell-shaped technique with little demonstrated runtime governance.
- **Practiced Trick** — reliable bounded effect with some grounding, but not enough for Level 0.
- **Master Trick** — excellent bounded technique that may be better left a Trick.
- **Level 0–9 Spell** — demonstrated casting range. Higher level means broader/deeper governed casting space, not higher quality.
- **Grade** — quality and reliability within the demonstrated range.
- **Mastery** — belongs to a caster/Familiar relationship, not to the Spell definition itself.

A blocked cast can be evidence of strong Spellcraft. A valid Spell that correctly refuses to cast is not a Trick.

## Repository shape

```text
protocol/
  SPELL.md                 # v0 protocol baseline
  spell.schema.json        # portable Spell definition contract
  cast.schema.json         # runtime cast state
  receipt.schema.json      # effect/evidence receipt
runtime/
  spell_runtime.py         # dependency-free reference validator/evaluator
spells/
  familiar/                # first native Spell
migration/
  agent-skills.md          # Skill -> Trick -> Spell migration path
  mcp.md                   # MCP capability bridge
```

## Compatibility stance

Spell is designed to compose with, not replace, the two protocols that most directly inspired it:

1. **Agent Skills** — portable folders centered on `SKILL.md`, with optional scripts, references, and assets, progressively disclosed to agents.
2. **Model Context Protocol (MCP)** — typed, discoverable capabilities and tool calls across stdio/HTTP, with per-request metadata, authorization, structured input/output schemas, explicit state handles, and extension negotiation.

A Skill can be upgraded into a Spell without throwing away `SKILL.md`. MCP tools can satisfy Spell telemetry, observation, execution, and evidence capabilities without becoming the Spell contract itself.

## Protocol sources frozen for this baseline

This v0 baseline was designed against the public specifications available on **2026-08-15**:

- Agent Skills specification: https://agentskills.io/specification
- Agent Skills reference repository: https://github.com/agentskills/agentskills
- MCP specification revision `2026-07-28`: https://modelcontextprotocol.io/specification/2026-07-28
- MCP extensions framework: https://modelcontextprotocol.io/extensions/overview

Spell is an independent experimental protocol and is not part of Agent Skills or MCP.

## First conformance targets

The protocol is intentionally being tested by two unlike Spells:

- **Familiar** — persistent, identity-bearing, historical, expressive.
- **Prestidigitation** — small, bounded, flexible, often ephemeral transformations.

If both can fit the same contract without one inheriting the accidental ontology of the other, the abstraction is probably healthy.
