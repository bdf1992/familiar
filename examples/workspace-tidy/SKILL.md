---
name: workspace-tidy
description: "Remove only files explicitly marked with the .agentspells-disposable suffix from an authorized workspace while preserving every other pre-existing file. Use as a deterministic cleanup Skill or as a Technique behind the workspace-tidy Agent Spell example."
---

# Workspace Tidy

Remove files whose names end in `.agentspells-disposable` beneath the requested workspace. Preserve every other file byte-for-byte.

This is an ordinary Agent Skill. It works without Agent Spells. When an Agent Spells host uses it as a Technique, the host remains responsible for telemetry, authority, limits, postconditions, and CAST emission.

## Procedure

1. Confirm the target is the intended workspace.
2. Run `python scripts/tidy.py <workspace>`.
3. Report the removed relative paths.
4. Do not claim broader cleanup than the script actually performs.

## Boundary

This Skill forbids deleting unmarked files, deleting directories, following directory symlinks for cleanup, or treating a successful script exit as proof of a wider workspace effect.
