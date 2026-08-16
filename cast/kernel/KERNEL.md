# Agent Spells Kernel 0.2

The Kernel is separate from the Agent Spells Format. It consumes a parsed `SPELL.md`, resolves a concrete caster and optional Familiar, obtains observations from the host environment, decides whether an effect may execute, observes execution, and emits a CAST record.

The kernel does not own Skill discovery, MCP transport, user identity stores, Familiar authorship, Spellcraft, or standing claims.

## Format validity
The kernel validates the SPELL frontmatter against the format schema and semantic reference rules before execution. This forbids executing a malformed or internally inconsistent declaration.

## Familiar validity
If a Familiar is supplied, the kernel validates it before use. Familiar participation is optional. A valid cast with no Familiar proceeds normally.

A Familiar may change guidance representation and attention cues. It must not change the selected effect, telemetry requirements, requirement checks, limits, authority resolution, executor behavior, or outcome classification. This forbids persona/dialect configuration from becoming hidden execution authority.

## Authority resolution
`SPELL.md` states authority needed by an effect. The kernel asks the host authority resolver whether this caster has each required authority in the current target context. CAST never accepts a caller-written `satisfied: true` as authority evidence. Familiar authority cannot grant missing caster authority.

## Closure
The kernel closes only when the declaration is valid, any supplied Familiar is valid, required telemetry is present/fresh, required authority resolves true, every `before` requirement has a checker and passes, and every referenced limit has a checker and passes. Otherwise closure is refused and execution does not run.

This forbids partial prerequisite satisfaction from being treated as permission to execute.

## Outcome classification
After closure the kernel executes the bound implementation, re-observes declared telemetry, evaluates `after` requirements, and re-checks limits.

- `resolved` — execution completed, postconditions passed, and limits remained satisfied;
- `partial` — execution completed but one or more declared postconditions could not be confirmed;
- `failed` — execution failed or a declared hard limit was violated after execution.

The kernel records post-execution observations even after executor failure when observation remains possible. A tool return or model statement is not sufficient proof of effect by itself.

## CAST is the receipt
There is no separate receipt artifact in 0.2. CAST is the durable execution record. It contains spell name/version, caster, optional Familiar id/guidance, selected effect, closure decision/reasons, observations, outcome, implementation result if available, and residuals. This forbids two competing records of the same execution truth.

## Residuals
A residual records a mismatch the declared effect did not resolve or could not verify. Unexpected post-execution observations are retained in the observation stream and may produce residuals; the core kernel does not need separate fantasy-specific failure types to preserve them. This forbids rewriting unexpected runtime behavior into the expected effect after the fact.

## MCP relationship
MCP may supply observers, checkers, authority-bearing capabilities, executors, and structured tool results. The kernel does not replace MCP transport or authorization.

Current MCP already defines structured tool results, output schemas, tool execution errors, and an authorization framework. Agent Spells adds a higher-level effect contract and execution record around one or more Skill/MCP operations; it must not claim that MCP lacks structured errors or authorization.

Source baseline: MCP specification revision 2026-07-28, https://modelcontextprotocol.io/specification/2026-07-28.
