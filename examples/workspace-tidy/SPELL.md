---
spell_format: "0.2"
name: workspace-tidy
version: "0.1.0"
description: Delete explicitly marked disposable files from a writable workspace while preserving every other pre-existing file byte-for-byte.
telemetry:
  - id: workspace-state
    description: Recursive file manifest containing relative path, digest, and disposable marker state.
    max_age_ms: 1000
limits:
  - id: preserve-unmarked
    description: Every pre-existing file not ending in .agentspells-disposable must remain present and byte-identical after execution.
effects:
  - id: tidy
    description: Delete every file ending in .agentspells-disposable and preserve every unmarked pre-existing file.
    telemetry: [workspace-state]
    requirements:
      - id: target-observable
        phase: before
        description: The target exists as an observable directory before execution.
      - id: disposable-absent
        phase: after
        description: No file ending in .agentspells-disposable remains after execution.
    limits: [preserve-unmarked]
    authority: [workspace.write]
---

# Workspace Tidy effect

This declaration does not select an implementation. The adjacent Agent Skill is one Technique a host may bind to `tidy`. A conforming host may use a different Skill, MCP tool, script, or service as long as the declared observations, authority, limit, and postcondition are independently evaluated.
