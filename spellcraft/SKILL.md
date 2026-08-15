---
name: spellcraft
description: Author, inspect, repair, and migrate Agent Spells SPELL.md declarations. Use when turning an existing Skill or MCP-backed capability into a portable effect declaration, separating caster preferences from runtime requirements, writing effect checks, or revising a declaration from CAST records. Spellcraft is an Agent Skill, not a Spell, and it is not present at cast time.
---

# Spellcraft

Spellcraft authors and repairs `SPELL.md`. It may work with no Agent Spells Kernel. When CAST records exist, use them as evidence; never copy standing or success claims into the declaration.

## Study the capability
Identify the smallest effects that a runtime could actually attempt and observe. Reuse existing Skills and MCP tools as implementation material rather than rewriting working competence.

A Familiar may assist the crafter with dialect, attention, preferences, and judgment. Familiar guidance is craft material, not a Spell requirement unless an independently checkable runtime requirement justifies the same constraint.

## Write only portable contract fields
Follow `../format/SPECIFICATION.md` and validate frontmatter against `../format/spell.schema.json`.

A declaration contains only name, version, description, telemetry declarations, limits, and effects; each effect declares required telemetry, before/after requirements, limits, and caster authority.

Do not add implementation bindings, magic words, caster preferences, standing, level, grade, energy, trial results, or execution receipts to `SPELL.md`.

## Distinguish before writing
- If the capability is primarily instructions or expertise, it stays a Skill.
- If it is one implementation procedure used to realize a larger effect, treat it as a Technique.
- If it only improves another cast and has no independently declared effect, treat it as a Buff.
- If it is caster-authored dialect/judgment configuration, it is a Familiar.
- Only write a SPELL declaration when there is an effect whose valid execution materially depends on runtime observations, authority, requirements, or limits and whose result can at least be investigated post hoc.

## Use CAST records to revise
A CAST record is the runtime receipt. Read closure reasons, observations, outcome, and residuals. Change `SPELL.md` only when runtime evidence shows the declaration is missing or misstating a real condition.

Do not improve apparent capability by changing description text. Improve the declaration by making its effects more falsifiable and its gates more accurate.

## Spellcraft forbids
- declaring level, grade, or standing;
- treating a Skill description as proof of runtime effect;
- encoding one caster's Familiar preferences as universal Spell requirements;
- encoding one implementation's dependencies as properties of the Spell unless every valid implementation requires them;
- adding a field that neither gates execution nor improves portable effect inspection.
