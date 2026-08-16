---
spell_format: "0.3-candidate"
name: find-familiar
version: "0.1.0"
description: Establish a validated Familiar artifact explicitly accepted for a resolved subject.
telemetry: []
effects:
  - id: establish
    description: Persist one schema-valid subject-owned Familiar accepted by that subject.
    telemetry: []
    requirements:
      before:
        - id: subject-resolved
          description: The subject whose Familiar is being found is explicitly resolved.
        - id: familiar-store-supported
          description: The environment can persist and resolve an exact Familiar artifact.
        - id: subject-accepted
          description: The subject explicitly accepted the complete Familiar candidate selected for persistence.
      during: []
      after:
        - id: familiar-valid
          description: The resulting artifact validates against the Familiar contract.
        - id: familiar-persisted
          description: The exact accepted Familiar can be resolved from its returned FamiliarRef.
---

# Find Familiar

A conforming Technique may use several Shapes, Parts, Features, and Marks before closure. Those drafts are preparation, not the Effect. The Effect occurs only after the subject accepts a complete candidate, closure succeeds, and the exact Familiar artifact is persisted for that subject.

The Owl Agent may conduct the cast using `owl.system` as its Familiar. Owl is not the resulting subject Familiar and cannot accept the Whole for the subject, grant authority, or waive Requirements.
