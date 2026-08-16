---
name: familiar-guidance
description: Apply a valid Familiar or Familiar View as bounded guidance for representation, attention, preferences, stake, and advisory judgment without granting runtime authority or changing Spell semantics. Use when a host or agent wants to work with a practitioner through an accepted Familiar or host-facing view.
---

# Familiar Guidance

Use Familiar material to shape how guidance is represented and what deserves attention while preserving the boundary between advisory configuration and runtime truth.

This is an Agent Skill, not a Spell. It produces no Effect by itself and grants no authority.

## Accepted inputs

Prefer one of:

1. an exact Familiar resolved from a valid `FamiliarRef`; or
2. a Familiar View whose `subject` identifies an exact Familiar revision and whose perspective is appropriate for this host or interaction.

A Familiar View is source-bounded representation. Treat omitted source material as unknown. Do not infer omitted Familiar state from conversation style, history, metadata, reports, or model confidence.

A Report about a Familiar is not automatically a Familiar View and is not a direct substitute for accepted Familiar guidance. Report statements may be useful knowledge, but durable guidance changes still require the Familiar's own acceptance path.

## Apply guidance

A Familiar or Familiar View may influence:

- **dialect** — wording, representation, notation, structure, and explanatory style;
- **attention** — which distinctions, risks, invariants, or opportunities receive deliberate inspection;
- **preferences** — how otherwise-valid options are ranked or presented;
- **stake** — what consequences matter to the practitioner and should be surfaced for judgment;
- **advisory authority** — which kinds of recommendations the Familiar is allowed to make confidently.

Apply these as guidance, not hidden execution rules.

## Preserve invariants

```text
Familiar guidance != runtime authority
Preference != Requirement
Attention != Telemetry
Stake != permission
View != Familiar
View != Report
Omission != absence
Report knowledge != Familiar state
```

Do not let Familiar material:

- alter a SPELL declaration;
- satisfy or waive a Requirement;
- fabricate Telemetry;
- grant caster or host authority;
- expand Scope;
- raise Cost or Duration ceilings;
- change Technique compatibility;
- reinterpret executor success as proof of Effect;
- change CAST outcome classification.

If a requested action depends on one of those mechanisms, surface the need for the appropriate Environment or Cast mechanism instead of pretending guidance can supply it.

## Familiar View handling

When consuming a Familiar View:

1. inspect the exact subject reference (`id`, `caster_id`, `revision`, `digest`);
2. require that the view was produced from a Familiar successfully resolved through that reference before representing it as exact;
3. respect the named policy and `for` perspective;
4. apply only the guidance actually present in the View;
5. treat fields named in `omitted` as unknown to this consumer;
6. never reconstruct omitted private material.

If provenance cannot establish that the subject reference was resolved when the View was produced, treat the material as attributed guidance rather than an exact Familiar View.

## Corrections

When the practitioner corrects a material dialect, attention, preference, stake, or advisory-authority statement, do not silently evolve the Familiar or View. Treat the correction as candidate source material for Find Familiar.

A host may adapt presentation transiently during a conversation. Durable Familiar changes require the Familiar's own acceptance and persistence path.
