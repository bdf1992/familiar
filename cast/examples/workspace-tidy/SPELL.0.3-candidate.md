---
spell_format: "0.3-candidate"
name: workspace-tidy
version: "0.2.0"
description: Delete explicitly marked disposable files from a writable workspace while preserving every other pre-existing file byte-for-byte.
telemetry:
  - id: workspace-state
    description: Recursive file manifest containing relative path, digest, and disposable marker state.
    max_age_ms: 1000
effects:
  - id: tidy
    description: Delete every file ending in .agentspells-disposable and preserve every unmarked pre-existing file.
    telemetry: [workspace-state]
    requirements:
      before:
        - id: target-observable
          description: The target exists as an observable directory before execution.
        - id: write-authority
          authority: workspace.write
      during:
        - id: execution-time
          duration:
            execution_max_ms: 1000
      after:
        - id: disposable-absent
          description: No file ending in .agentspells-disposable remains after execution.
        - id: preserve-unmarked
          description: Every pre-existing unmarked file remains present and byte-identical after execution.
---

# Workspace Tidy candidate

This file exercises the requirement-centered draft and does not replace the 0.2 compatibility declaration yet.

The adjacent Agent Skill remains one Technique. The Spell does not contain the script instructions or Python dependency. The 0.4 Technique Binding states which runtime controls that implementation participates in.
