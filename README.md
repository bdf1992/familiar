# Agent Spells

Agent Spells pairs a **portable `SPELL.md` format** with a **small execution Kernel** that validates live requirements around Skill/MCP execution and emits a machine-consumable CAST record.

The two deliverables are deliberately separate:

- `format/` — what a portable `SPELL.md` declares;
- `kernel/` — runtime validation, observation, authority resolution, execution closure, outcome classification, and CAST records.

Familiar is not the umbrella system and is not a Spell. A **Familiar** is a caster-owned dialect/judgment artifact. **Find Familiar** is the Agent Skill that creates and repairs Familiar artifacts. **Spellcraft** is the Agent Skill that creates and repairs `SPELL.md` declarations.

Nothing in this repository currently has demonstrated Spell standing. The included tests are synthetic conformance fixtures for the reference Kernel.

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
migration/
  agent-skills.md
  mcp.md
  draw-the-owl.md
tests/
  fixtures/
  test_kernel.py
```

## Test

```bash
python -m pip install PyYAML jsonschema
python -m unittest discover -s tests -v
```

The six baseline fixtures cover closure/refusal, malformed Familiar rejection, Familiar interchangeability, executor failure with post-observation, and a machine caster receiving a JSON-serializable CAST record.

## Source baselines

Reviewed 2026-08-15:

- Agent Skills specification: https://agentskills.io/specification
- MCP specification revision 2026-07-28: https://modelcontextprotocol.io/specification/2026-07-28
- MCP 2026-07-28 release notes: https://blog.modelcontextprotocol.io/posts/2026-07-28/

Agent Spells is an independent experimental protocol and is not part of Agent Skills or MCP.
