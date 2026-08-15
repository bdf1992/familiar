# Agent Skill -> Trick -> Spell

Baseline date: 2026-08-15.

Source specification: https://agentskills.io/specification

## What we inherit

The current Agent Skills format is intentionally lightweight:

```text
skill-name/
├── SKILL.md
├── scripts/       # optional
├── references/    # optional
├── assets/        # optional
└── ...
```

`SKILL.md` contains YAML frontmatter plus Markdown instructions. `name` and `description` are required; optional fields include `license`, `compatibility`, `metadata`, and experimental `allowed-tools`.

Agent Skills also defines progressive disclosure:

1. load name + description in the catalog;
2. load the full `SKILL.md` when activated;
3. load scripts/references/assets only as needed.

Spell SHOULD preserve this packaging advantage.

## Migration principle

> Upgrade the claims around competence; do not throw away the competence.

A working Skill can remain a valid Agent Skill while gaining a sibling `SPELL.json` contract and Spell-specific trials.

Recommended dual-compatible layout:

```text
my-capability/
├── SKILL.md               # existing Agent Skill, unchanged when possible
├── SPELL.json             # Spell definition / claims
├── scripts/               # existing implementation
├── references/            # existing knowledge
├── assets/                # existing assets
└── trials/                # Spell demonstrations
```

A Spell-aware host loads `SPELL.json`. A Skill-only host continues using `SKILL.md`.

## Stage 1 — Skill

Keep the original Skill valid and useful.

Example:

```yaml
---
name: workspace-cleanup
description: Clean temporary and generated files from a software workspace. Use when asked to tidy or clean a project directory.
---
```

Its scripts may already be excellent. Nothing about Spell requires degrading or renaming them.

## Stage 2 — Trick

Identify one bounded, recognizable effect already produced by the Skill.

Example:

```text
Expression: tidy
Effect: remove proven cache artifacts and normalize selected generated files
Evidence: before/after manifest + diff
```

At this stage the capability may be a Novice, Practiced, or Master Trick.

The magic-facing invocation MAY be added:

```text
Prestidigitation: tidy this workspace
```

But magic vocabulary alone does not improve standing.

## Stage 3 — Level 0 candidate

Add a Spell definition that declares what must be observed and governed around the existing implementation.

Example additions:

```json
{
  "telemetry": {
    "required": ["workspace_manifest", "write_authority", "version_control_state"]
  },
  "requirements": [
    "target scope is observable"
  ],
  "limits": [
    "do not publish externally",
    "do not destroy authored files"
  ],
  "energy": {
    "resources": ["scope", "verification"]
  }
}
```

The existing Skill script can still perform the actual cleanup.

## Stage 4 — Trial

Demonstrate that the new contract changes behavior.

At minimum, a Level 0 migration SHOULD include contrastive trials such as:

```text
clean workspace           -> apply bounded cleanup
workspace with dirty code -> preserve authored changes / reduce effect
read-only workspace       -> preview only or block
missing required state    -> block or probe
forbidden target          -> refuse
```

If all cases produce effectively the same behavior, the Spell wrapper is decorative and the implementation remains a Trick.

## Stage 5 — Demonstrated Spell

A runtime may assign demonstrated standing only after trial evidence shows:

- relevant telemetry affects valid casting;
- requirements are enforced;
- limits are enforced;
- claimed effects are evidenced;
- missing prerequisites produce correct blocking/reduction rather than confident improvisation.

The original Skill remains implementation material.

## Field mapping

| Agent Skills | Spell |
|---|---|
| `name` | `identity.id` / `identity.name` |
| `description` | catalog description; can summarize `inherent_ability` |
| `compatibility` | environment hint; Spell runtime still observes actual telemetry |
| `metadata` | may point to Spell package/version; not authoritative runtime state |
| `allowed-tools` | host preapproval hint; does not replace Spell authority/limits |
| Markdown instructions | implementation guidance / technique |
| `scripts/` | Tricks, probes, adapters, effect implementations |
| `references/` | study material / domain knowledge |
| `assets/` | icons, templates, examples, output materials |
| progressive disclosure | retained; Spell definition should stay compact and resources stay lazy |

## What must not be inferred during migration

A Skill field is not automatically stronger just because Spell has a similar concept:

- `compatibility` is not live telemetry;
- `allowed-tools` is not proof of authority for a particular consequential action;
- a script succeeding once is not a demonstrated range;
- an instruction saying "verify" is not effect evidence;
- a long prompt is not energy governance;
- a polished magical name is not a Spell.

## Exit criteria

A migration is successful when:

1. the original Skill still works in Skill-only hosts;
2. the Spell definition validates;
3. at least one existing Skill effect is represented as an Expression;
4. live conditions materially constrain or alter casting;
5. a receipt can show what happened and why the effect may be trusted;
6. demonstrated standing is earned by Trials rather than copied from a declared claim.
