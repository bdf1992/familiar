---
spell_format: "0.3-candidate"
name: bounded-work
version: "0.0.0"
description: Attempt one bounded unit of work under observable authority, scope, cost, duration, and postcondition requirements.
telemetry: []
effects:
  - id: act
    description: Perform the requested bounded action and confirm the resulting condition.
    telemetry: []
    requirements:
      before:
        - id: target-observable
          description: The requested target is observable.
        - id: write-authority
          authority: workspace.write
        - id: bounded-scope
          scope:
            max_items: 2
      during:
        - id: tool-budget
          cost:
            resource: tool_calls
            max: 1
        - id: execution-time
          duration:
            execution_max_ms: 50
      after:
        - id: effect-confirmed
          description: The requested bounded action is observable as complete.
---

# Candidate only

This declaration is an experimental structural fixture. FORMAT 0.2 remains normative.

The experiment asks whether Authority, Scope, Cost, and Duration need peer Spell fields, or whether they can be machine-readable forms of Requirements while retaining dedicated Kernel enforcement mechanisms.

Cost and Duration are deliberately `during` Requirements: their budgets are established before execution, but compliance is governed while execution is occurring.
