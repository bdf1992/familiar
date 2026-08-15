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
    description: Remove temporary artifacts and confirm that authored files remain unchanged.
    telemetry: [workspace-state]
    requirements:
      - id: target-observable
        phase: before
        description: The target workspace can be observed.
      - id: tidy-confirmed
        phase: after
        description: Temporary artifacts are absent after execution.
    limits: [preserve-authored]
    authority: [workspace.write]
---

# Workspace Tidy

The body is implementation guidance and examples. The portable contract is the frontmatter.
