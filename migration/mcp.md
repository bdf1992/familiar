# MCP -> Agent Spells Kernel 0.2

MCP is a capability and transport substrate. It does not need to become an Agent Spells protocol implementation.

A Kernel adapter may use MCP for telemetry observers, requirement/limit checkers, effect executors, structured tool output used as an observation, host authorization evidence, and explicit state handles.

Current MCP already defines structured JSON-RPC errors, tool execution errors, structured tool output/output schemas, and authorization. Agent Spells must not claim otherwise.

The additional Agent Spells responsibility is semantic composition: a `SPELL.md` effect may span one or more MCP operations, and the Kernel records whether the effect's declared preconditions/postconditions were observed, not merely whether the individual tool call returned successfully.

MCP 2026-07-28 is stateless at the protocol layer. Durable Spell application state should use explicit handles/records rather than hidden transport-session state.

Source baseline: https://modelcontextprotocol.io/specification/2026-07-28 and https://blog.modelcontextprotocol.io/posts/2026-07-28/.
