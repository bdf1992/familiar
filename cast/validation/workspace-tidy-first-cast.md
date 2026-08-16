# Workspace Tidy — First External-Effect Validation

Date: 2026-08-15.

This is the first Agent Spells integration in this repository where the Kernel governs a Technique that mutates an actual filesystem rather than a synthetic in-memory executor.

## What ran

`examples/workspace-tidy/SKILL.md` remains an ordinary Agent Skill. Its `scripts/tidy.py` implementation is bound by the example host as a Technique for the `tidy` effect declared in `SPELL.md`.

The integration fixture creates a temporary workspace containing two explicitly disposable files and two unmarked files. The Kernel observes a before manifest, resolves `workspace.write`, checks the target and preservation limit, invokes the Skill script as a subprocess, observes the workspace again, checks the declared postcondition, and emits CAST.

This mechanism forbids treating the script's zero exit code or its own `removed` list as proof that the declared effect occurred. The after observation and postcondition are independent of the script result.

## Perception ledger

| Effect | Observable in this fixture? | Confirmation | Remaining gap |
|---|---|---|---|
| `workspace-tidy/tidy` | Yes | Before/after filesystem manifest, `disposable-absent` after requirement, `preserve-unmarked` limit, CAST outcome | Only one reference host/Technique and ephemeral CI filesystem have been exercised; no broad standing follows |

The denied-authority fixture also confirms that the Kernel refuses closure before the Technique runs when `workspace.write` is absent.

## What this validates

- A Skill can remain independently usable while serving as a Technique behind a portable Spell effect.
- `SPELL.md` does not need to name the Skill implementation.
- The host binding can be replaced without changing the declaration.
- The Kernel can observe a concrete external state change and distinguish implementation success from effect confirmation.
- A cast can execute with no Familiar supplied.
- CAST is machine-consumable and can be compared against a durable expected record.

## What this does not validate

- Spell standing, level, grade, or reliability across environments.
- Semantic correctness of arbitrary host observers/checkers.
- MCP composition.
- Multi-Technique composition.
- Familiar guidance under a real effectful cast.
- Partial outcome behavior against a real external effect.

No Spell standing is claimed. This fixture moves one effect from `unobservable` to `observed in the reference integration environment`; it does not establish that `workspace-tidy` is a demonstrated Spell.
