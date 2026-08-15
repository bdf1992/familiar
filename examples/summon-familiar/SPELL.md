---
spell_format: "0.3"
name: summon-familiar
version: "0.1.0"
description: Establish bounded Presence of an independently existing Familiar in the current casting context.
telemetry: []
effects:
  - id: summon
    description: Make the resolved Familiar present in the current session without creating or mutating it.
    telemetry: []
    requirements:
      before:
        - id: target-exists
          description: The requested Familiar already exists independently of this cast.
        - id: target-is-familiar
          description: The resolved target validates against the Familiar contract.
        - id: target-identity-resolved
          description: The resolved Familiar id exactly matches the requested target reference.
        - id: presence-supported
          description: The host exposes a bounded session Presence mechanism.
      during: []
      after:
        - id: target-present
          description: The requested Familiar is present in the current session.
        - id: identity-preserved
          description: The summoned Familiar preserves the pre-cast identity and owner/caster record.
---

# Summon Familiar

This Spell does not create a Familiar. The target must already exist and resolve before closure. A conforming Technique establishes bounded session Presence; after checks independently confirm Presence and identity preservation.
