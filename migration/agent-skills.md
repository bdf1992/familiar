# Agent Skills -> Agent Spells 0.2

Agent Spells does not replace Agent Skills. A working Skill usually stays a Skill.

1. Keep `SKILL.md` unchanged while the Skill remains useful independently.
2. Identify a concrete effect larger than the Skill instructions themselves.
3. If the Skill is one way to realize that effect, classify it as a **Technique** and keep it as the implementation body.
4. Write a separate `SPELL.md` only when attempting the effect materially depends on live telemetry, caster authority, requirements, or limits and the result can be investigated after execution.
5. Bind the Skill/Technique to the effect in the host/kernel implementation, not in portable `SPELL.md`.
6. Run through the Kernel and accumulate CAST records. Do not declare Spell standing from migration intent.

A Skill-only host can ignore `SPELL.md`. A Spell-aware host may use the Skill as a Technique after separately loading the declaration.

Source baseline: https://agentskills.io/specification (2026-08-15).
