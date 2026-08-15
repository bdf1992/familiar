# Protocol source baseline — 2026-08-15

Spell v0 deliberately borrows from existing protocols instead of pretending to start from zero.

## Agent Skills

Primary source: https://agentskills.io/specification

Implementation guide: https://agentskills.io/client-implementation/adding-skills-support

The 2026-08-15 Agent Skills baseline used here includes:

- a skill is a directory with required `SKILL.md`;
- `SKILL.md` is YAML frontmatter plus Markdown instructions;
- required frontmatter: `name`, `description`;
- optional frontmatter includes `license`, `compatibility`, `metadata`, and experimental `allowed-tools`;
- optional `scripts/`, `references/`, and `assets/` directories;
- progressive disclosure from catalog metadata, to full instructions, to on-demand resources;
- `skills-ref validate` for reference-format validation.

Spell inherits the low-friction package shape and progressive disclosure model. Spell does **not** reinterpret `compatibility` or `allowed-tools` as live telemetry or cast authority.

## Model Context Protocol

Primary release baseline: https://blog.modelcontextprotocol.io/posts/2026-07-28/

Specification: https://modelcontextprotocol.io/specification/2026-07-28

Extensions: https://modelcontextprotocol.io/extensions/overview

JSON Schema default dialect: https://modelcontextprotocol.io/seps/1613-establish-json-schema-2020-12-as-default-dialect-f

The MCP `2026-07-28` baseline used here includes:

- stateless protocol core;
- retired protocol-level `initialize`/`initialized` session handshake for the modern revision;
- self-describing per-request client/protocol capability metadata;
- optional `server/discover` capability discovery;
- explicit application state handles rather than hidden protocol-session state;
- header-based routing for Streamable HTTP;
- cache hints on list/read results;
- Multi Round-Trip Requests for in-band additional input;
- authorization hardening;
- formal extension framework;
- Tasks as an extension rather than core;
- Roots, Sampling, and Logging deprecated for new implementations;
- JSON Schema 2020-12 as the default dialect for embedded schemas.

Spell inherits MCP's capability composition, structured schemas, authorization substrate, explicit-state bias, and extension discipline. Spell does **not** redefine MCP transport.

## The gap Spell is exploring

Neither source protocol currently defines the combination Spell needs as its primary contract:

```text
expressive invocation
+ live telemetry
+ requirements
+ hard limits
+ variable resource/energy commitment
+ effect evidence
+ contrastive Trials
+ demonstrated Trick/Level/Grade standing
```

That gap is the experimental scope of Spell.

## Compatibility promise

Spell v0 aims for these migration properties:

1. a valid Agent Skill can remain valid after a Spell wrapper is added;
2. existing Skill scripts/references/assets can remain implementation material;
3. an MCP server can remain an ordinary MCP server while serving Spell casts;
4. Spell state can cross MCP calls using explicit handles/receipts rather than transport sessions;
5. future Spell-over-MCP wire conventions should use the MCP extension mechanism rather than silently forking MCP.
