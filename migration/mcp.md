# MCP -> Spell Runtime Bridge

Baseline date: 2026-08-15.

Primary sources:

- MCP 2026-07-28 release/specification overview: https://blog.modelcontextprotocol.io/posts/2026-07-28/
- MCP documentation/specification: https://modelcontextprotocol.io/specification/2026-07-28
- MCP extensions: https://modelcontextprotocol.io/extensions/overview

## What we inherit

Spell should reuse MCP where MCP is already strong:

- typed tool discovery and invocation;
- resource discovery/reading;
- structured input/output schemas;
- authorization and per-request capability surfaces;
- stdio and HTTP transports;
- explicit capability discovery;
- extension negotiation;
- long-running work through the Tasks extension where supported;
- user input during a call through the modern multi-round-trip model where supported.

Spell is not a competing transport protocol.

## 2026-07-28 compatibility rule

The 2026-07-28 MCP core is stateless at the protocol layer. The legacy `initialize`/`initialized` exchange and protocol session identifier were retired. Requests are self-describing; clients can optionally call `server/discover`. Application state remains possible, but current MCP guidance is to represent it explicitly with handles passed between requests rather than hidden transport-session state.

Spell follows that model.

A cast, Familiar registration, long-horizon continuation, or Trial MAY have durable state, but that state MUST be represented by explicit Spell/runtime identifiers or handles. A Spell MUST NOT depend on an implicit MCP transport session for identity or continuity.

## Layering

```text
Human / Agent
     |
     v
Spell Runtime
  - definition validation
  - cast validation
  - telemetry binding
  - requirements
  - limits
  - energy
  - trials
  - standing
  - receipts
     |
     +-------------------+
     |                   |
     v                   v
MCP client            local adapters
     |
     v
MCP servers
  - tools
  - resources
  - prompts if useful
  - extensions
```

MCP supplies capabilities. Spell governs whether, why, and under what contract those capabilities may participate in a cast.

## Mapping

| MCP concept | Spell use |
|---|---|
| tool | probe, telemetry provider, Trick implementation, or effect mechanism |
| tool input schema | validates one capability call; may satisfy part of a Spell Expression |
| tool output / structured content | telemetry, effect data, or evidence depending on provenance |
| resource | study material, current state, artifact, evidence, or context source |
| prompt | optional implementation/casting aid; not the Spell contract |
| server discovery | capability observation for a cast/runtime |
| authorization | contributes to authority evidence; Spell can impose narrower limits |
| explicit state handle | compatible with cast, continuation, task, or artifact handles |
| task extension | possible carrier for long-running cast execution |
| input-required / MRTR | possible mechanism for missing user input or approval |
| extension negotiation | possible future home for Spell-specific MCP interop |

## Telemetry bridge

A Spell telemetry item should be able to cite an MCP call as provenance without embedding MCP-specific assumptions into the Spell definition.

Example runtime observation:

```json
{
  "name": "git_status",
  "value": {"dirty": true},
  "source": {
    "kind": "mcp-tool",
    "server": "local-dev",
    "tool": "git_status"
  },
  "observed_at": "2026-08-15T10:30:00-05:00",
  "coverage": "repository",
  "freshness_ms": 250
}
```

The Spell definition asks for `git_status`. An adapter decides whether that comes from MCP, a local process, a host API, or another authorized source.

## Tool annotations are hints, not Spell limits

MCP tools may expose descriptive/behavioral annotations. Spell SHOULD use them as useful hints, but MUST NOT treat untrusted or descriptive annotations as authoritative proof that a call is safe for a particular cast.

For example, a read-only hint may help planning, but Spell still evaluates:

- caster authority;
- target scope;
- consequence;
- Spell-specific limits;
- required evidence.

## Authorization layering

MCP authorization answers whether a caller may access a server/capability under the transport's security model.

Spell authorization is narrower and contextual:

```text
MCP says: this caller may invoke `deploy`.
Spell says: this cast may deploy only to staging, only after fresh tests,
            and only within the stated energy/consequence limit.
```

A Spell MUST NOT widen MCP/host authority. It MAY narrow it.

## Effect evidence

An MCP tool returning success is not automatically enough evidence for a Spell effect.

The Spell definition declares what evidence is appropriate. For example:

```text
Tool response: "deployment requested"       != deployment effect
Deployment receipt + observed healthy state  = stronger effect evidence
```

The runtime may use one MCP call to enact an effect and another to verify it.

## Spell-specific MCP extension: later, not v0

MCP now has a formal extension mechanism. A future Spell extension could advertise concepts such as:

- Spell-aware tool metadata;
- telemetry provenance envelopes;
- cast receipt resources;
- Trial endpoints;
- Spellbook discovery;
- Familiar participation hints.

Do not standardize this in v0. First prove the Spell model outside MCP-specific wire semantics. If interop demand emerges, define an extension using the MCP extension process and explicit opt-in/fallback rules.

## Migration path for an MCP server

An existing MCP server does not need to become a Spell server.

Progression:

1. Keep the MCP server unchanged.
2. Reference its tools/resources from a Spell runtime adapter.
3. Define which calls provide telemetry, effects, or evidence.
4. Add Spell Trials around combinations of calls and changed runtime conditions.
5. Only later add Spell-specific metadata/extension support if it materially improves interop.

## Exit criteria

The bridge is healthy when:

- the same Spell can use MCP or non-MCP capabilities without changing its inherent ability;
- no Spell depends on hidden protocol-session state;
- MCP authorization is never widened by Spell;
- telemetry provenance survives capability boundaries;
- effects are evidenced independently of persuasive model output;
- unsupported Spell-specific extensions degrade to ordinary MCP capability use.
