# Agent Spells Format 0.2

The Agent Spells Format defines the portable contents of `SPELL.md`. It does not define a runtime, transport, executor, standing system, or persistence model.

A `SPELL.md` remains meaningful without an Agent Spells Kernel: a host can catalog the declaration, inspect the effects it claims, see what telemetry and authority each effect requires, and decide whether it has an implementation capable of satisfying those declarations. Without a kernel or equivalent host implementation, none of those claims are mechanically verified.

## File shape

`SPELL.md` begins with YAML frontmatter and may contain Markdown after the closing frontmatter delimiter. The frontmatter is the portable declaration. The Markdown body is optional human guidance and is not part of kernel closure or effect verification.

```yaml
---
spell_format: "0.2"
name: workspace-tidy
version: "0.1.0"
description: Remove temporary workspace artifacts without modifying authored files.
telemetry:
  - id: workspace-state
    description: Current workspace manifest and dirty-file state.
    max_age_ms: 1000
limits:
  - id: preserve-authored
    description: Authored files must remain unchanged.
effects:
  - id: tidy
    description: Remove temporary artifacts and confirm authored files remain unchanged.
    telemetry: [workspace-state]
    requirements:
      - id: target-observable
        phase: before
        description: The target can be observed before execution.
      - id: tidy-confirmed
        phase: after
        description: Temporary artifacts are absent after execution.
    limits: [preserve-authored]
    authority: [workspace.write]
---
```

## Required fields

### `spell_format`
Machine format version. A host must reject a version it does not support. It forbids silently interpreting a declaration under incompatible semantics.

### `name`
Stable portable identifier used in catalogs and CAST records. It forbids anonymous execution records that cannot be tied back to a declaration.

### `version`
Version of this declaration. It forbids treating materially different declarations as the same executable contract.

### `description`
Human/catalog description of the capability. It is author-asserted and is not proof that an implementation behaves accordingly. Its role is selection and inspection, analogous to the description field in Agent Skills.

### `telemetry`
Named observations that effects may require. Each item declares an id, human description, and optional maximum age. It forbids an effect from closing when required state cannot be observed with the declared freshness.

### `limits`
Named boundaries that effects may reference. A declaration does not encode arbitrary limit logic; the executing host must provide a checker for each referenced limit. It forbids closing a cast when a referenced limit cannot be checked or is already violated.

### `effects`
The only executable claims in the format. Each effect declares an id, description, required telemetry, before/after requirements, limits, and caster authority. A `before` requirement gates closure. An `after` requirement is part of effect confirmation. If an after requirement cannot be checked, the effect remains unconfirmed and CAST carries a residual.

This forbids a declaration from substituting prose confidence for runtime preconditions or postconditions.

## Semantic validation

In addition to JSON Schema validation of the extracted frontmatter, telemetry ids, limit ids, effect ids, and requirement ids must be unique in their scopes; every effect telemetry reference must resolve to declared telemetry; and every effect limit reference must resolve to a declared limit.

## Not in the portable format

The following were removed from the earlier 0.1 draft because they were runtime state, implementation detail, or decorative claims:

- inherent ability — absorbed by `description` plus declared effects;
- magic words / invocation — host user interface, not execution semantics;
- expressions — absorbed by declared effects;
- energy — concrete resource state becomes telemetry and resource ceilings become limits;
- top-level evidence — effect confirmation is represented by `after` requirements and CAST observations;
- evaluation, trials, claimed level, grade, standing — derived from execution records and external test suites;
- compatibility / implementation binding — belongs to the host, Skill package, MCP server, or deployment that realizes the declaration.

## Relationship to Agent Skills

Agent Skills specifies a portable `SKILL.md` folder format and progressive loading model. Agent Spells deliberately copies the useful separation between catalog metadata and optional human instructions, but adds executable effect declarations. Agent Spells does not replace Agent Skills: a Skill can be one implementation used by a kernel to realize an effect.

Source baseline: https://agentskills.io/specification (reviewed 2026-08-15).
