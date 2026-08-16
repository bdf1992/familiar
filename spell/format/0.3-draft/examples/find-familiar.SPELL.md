---
spell_format: "0.3"
name: find-familiar
version: "0.2.0"
description: Establish a schema-valid Familiar explicitly accepted for a resolved subject and return an exact reference.

schemas:
  - id: familiar
    description: Persisted Familiar artifact.
    ref: ../../../../familiar/familiar.schema.json
  - id: familiar-ref
    description: Exact reference returned by Familiar persistence.
    schema:
      type: object
      additionalProperties: false
      required: [id, caster_id, revision, digest]
      properties:
        id: {type: string}
        caster_id: {type: string}
        revision: {type: integer, minimum: 1}
        digest: {type: string}

protocols:
  - id: familiar-store
    ref: familiar.store:FamiliarStore
    version: "0.1"
    operations:
      - id: put
        description: Persist one validated caster-owned Familiar and return its exact reference.
        input: {schema: familiar}
        result: {schema: familiar-ref}
      - id: resolve
        description: Resolve an exact Familiar reference back to the same artifact or fail noticeably.
        input: {schema: familiar-ref}
        result: {schema: familiar}

runtime:
  protocols: [familiar-store]

telemetry: []

implementations:
  - id: local-familiar-store
    kind: package
    locator: familiar.store:FamiliarStore
    effects: [establish]
    protocols: [familiar-store]
    description: Existing local reference implementation for exact Familiar persistence.

effects:
  - id: establish
    description: Persist only the explicitly accepted Familiar candidate for the resolved subject and return its exact reference.
    telemetry: []
    interface:
      result: {schema: familiar-ref}
    requirements:
      before:
        - id: subject-resolved
          description: The subject whose Familiar is being found is explicitly resolved.
          check: subject.resolved
          binding:
            operation: observe
            capability: subject-resolution

        - id: subject-accepted
          description: The resolved subject explicitly accepted the complete candidate selected for persistence.
          check: subject.accepted
          binding:
            operation: confirm
            capability: subject-acceptance
            subject: caster

        - id: familiar-store-supported
          description: The Environment exposes the declared Familiar store protocol.
          check: familiar.store.available
          binding:
            operation: put
            protocol: familiar-store
            capability: familiar-store

      during: []

      after:
        - id: familiar-valid
          description: The resulting Familiar validates against the declared Familiar schema.
          check: schema.valid
          binding:
            operation: validate
            capability: schema-validator

        - id: familiar-persisted
          description: The exact accepted Familiar resolves from the returned FamiliarRef.
          check: familiar.store.roundtrip
          binding:
            operation: resolve
            protocol: familiar-store
            capability: familiar-store
---

# Find Familiar — FORMAT 0.3 specimen

This specimen exercises the 0.3 contract surfaces needed by the first Familiar path. Preparation may generate or redraw many candidates, but only an explicitly accepted complete candidate may cross into persistence. The implementation suggestion is discoverability guidance; it does not grant authority or satisfy any Requirement by itself.
