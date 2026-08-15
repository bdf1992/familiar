---
spell_format: "0.3-candidate"
name: find-familiar
version: "0.1.0"
description: Establish a validated Familiar artifact explicitly authored or accepted by the caster.
telemetry: []
effects:
  - id: establish
    description: Persist one schema-valid caster-owned Familiar accepted by the target caster.
    telemetry: []
    requirements:
      before:
        - id: caster-resolved
          description: The practitioner/caster whose Familiar is being found is explicitly resolved.
        - id: familiar-store-supported
          description: The environment can persist and resolve an exact Familiar artifact.
      during: []
      after:
        - id: familiar-valid
          description: The resulting artifact validates against the Familiar contract.
        - id: caster-accepted
          description: The caster explicitly accepted the resulting Familiar candidate.
        - id: familiar-persisted
          description: The exact accepted Familiar can be resolved from its returned FamiliarRef.
---

# Find Familiar

A conforming practitioner Technique may use several Shapes, Parts, Features, and Marks before closure. Those drafts are preparation, not the Effect. The Effect occurs only after the caster accepts a complete candidate, closure succeeds, and the exact Familiar artifact is persisted.

The system Owl may advise the drawing when present. Owl is not the resulting caster Familiar and cannot grant authority or waive Requirements.
