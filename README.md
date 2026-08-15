# Agent Spells

Agent Spells pairs a **portable `SPELL.md` format** with a **small execution Kernel** that validates live requirements around Skill/MCP execution and emits a machine-consumable CAST record.

The two deliverables remain separate:

- **Spell / FORMAT** — what a portable `SPELL.md` declares;
- **SpellCast / KERNEL** — runtime validation, observation, authority resolution, execution closure, outcome classification, and CAST records.

Familiar is not the umbrella system and is not a Spell. A **Familiar** is a caster-owned dialect and judgment artifact. **Owl** is the protocol-aware system Familiar used to help create and inspect other Familiars. **Find Familiar** is the Agent Skill that performs that work. **Spellcraft** is an Agent Skill for authoring and repairing `SPELL.md`, but it is intentionally downstream of Owl and Familiar.

## Build order

Current priority is:

1. **Spell** — stabilize the portable declaration format and effect semantics.
2. **Owl** — stabilize the system Familiar that knows the protocol and can inspect Familiar quality.
3. **Familiar** — stabilize the caster-owned schema and use Find Familiar to create a real caster Familiar.
4. **Spellcraft** — author the Skill using the Spell format plus Owl and the caster Familiar as guidance.
5. **SpellCast** — continue the runtime Kernel after the authoring foundations are proven.

Spellcraft works over the Spell format, existing Skills/MCP capabilities, and optional evidence from prior CAST records. It does not require SpellCast in order to author a declaration. When SpellCast exists, its records can be used to repair that declaration from observed execution.

## Derived descriptions, not author labels

`SPELL.md` does not contain author-asserted standing or category fields such as `spell`, `trick`, `buff`, level, or grade. Those descriptions may only be derived later from validated structure and execution records.

`Buff` currently has a useful proposed definition but **zero instances**. It is therefore not a core artifact or an authored classification in the current protocol. If later structure or CAST evidence demonstrates a distinct modifier-only role, SpellCast may derive that description without adding a `buff: true` assertion to declarations.

Nothing in this repository currently has demonstrated Spell standing. The baseline tests validate Kernel mechanics, and `examples/workspace-tidy/` is a reference Skill-as-Technique integration with a measurable filesystem effect. It remains validation material rather than the current design priority.

## Repository

```text
AGENT_SPELLS.md
format/
  SPECIFICATION.md
  spell.schema.json
kernel/
  KERNEL.md
  spell_kernel.py
  cast.schema.json
owl/
  owl.json
familiar/
  familiar.schema.json
find-familiar/
  SKILL.md
spellcraft/
  SKILL.md
examples/
  workspace-tidy/
migration/
validation/
tests/
```

## Test

```bash
python -m pip install PyYAML jsonschema
python -m unittest discover -s tests -v
```

## Source baselines

Reviewed 2026-08-15:

- Agent Skills specification: https://agentskills.io/specification
- MCP specification revision 2026-07-28: https://modelcontextprotocol.io/specification/2026-07-28
- MCP 2026-07-28 release notes: https://blog.modelcontextprotocol.io/posts/2026-07-28/

Agent Spells is an independent experimental protocol and is not part of Agent Skills or MCP.

See [AGENT_SPELLS.md](AGENT_SPELLS.md) for the structural validation and 0.2 baseline.
