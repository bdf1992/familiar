# Agent Spells

Agent Spells pairs a **portable `SPELL.md` format** with a **small execution Kernel** that validates live requirements around Skill/MCP execution and emits a machine-consumable CAST record.

The two deliverables are deliberately separate:

- `format/` — what a portable `SPELL.md` declares;
- `kernel/` — runtime validation, observation, authority resolution, execution closure, outcome classification, and CAST records.

Familiar is not the umbrella system and is not a Spell. A **Familiar** is a caster-owned dialect/judgment artifact. **Find Familiar** is the Agent Skill that creates and repairs Familiar artifacts. **Spellcraft** is the Agent Skill that creates and repairs `SPELL.md` declarations.

Nothing in this repository currently has demonstrated Spell standing. The baseline tests validate Kernel mechanics, and `examples/workspace-tidy/` is the first real Skill-as-Technique integration fixture with a measurable filesystem effect.

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
familiar/
  familiar.schema.json
  owl.json
find-familiar/
  SKILL.md
spellcraft/
  SKILL.md
examples/
  workspace-tidy/
    SKILL.md
    SPELL.md
    host.py
    scripts/tidy.py
migration/
  agent-skills.md
  mcp.md
  draw-the-owl.md
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
