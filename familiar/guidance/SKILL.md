---
name: familiar-guidance
description: Apply a valid Familiar or Familiar View as bounded guidance for representation, attention, preferences, stake, and advisory judgment without granting runtime authority, establishing Presence, or changing Spell semantics. Use when a host or agent wants to work with a practitioner through accepted Familiar guidance.
---

# Familiar Guidance

Use Familiar material to shape how guidance is represented and what deserves attention while preserving the boundary between advisory configuration and runtime truth.

This is an Agent Skill, not a Spell. It produces no Effect by itself, establishes no Familiar Presence, and grants no authority.

## Accepted inputs

Prefer one of:

1. an exact Familiar resolved from a valid `FamiliarRef`; or
2. a Familiar View whose `subject` identifies an exact accepted Familiar revision and whose perspective is appropriate for this host or interaction.

When using a View, treat omitted source material as unknown. Do not infer omitted Familiar state from conversation style, history, metadata, or model confidence.

Possessing a View does not prove that the Familiar is Present. Presence is established separately by the host/runtime, such as through a conforming `Summon Familiar` cast.

## Apply guidance

A Familiar or View may influence:

- **dialect** — wording, representation, notation, structure, and explanatory style;
- **attention** — which distinctions, risks, invariants, or opportunities receive deliberate inspection;
- **preferences** — how otherwise-valid options are ranked or presented;
- **stake** — what consequences matter to the practitioner and should be surfaced for judgment;
- **advisory authority** — which kinds of recommendations the Familiar is allowed to make confidently.

Apply these as guidance, not hidden execution rules.

## Preserve invariants

```text
Familiar guidance != runtime authority
Familiar View != Familiar Presence
Preference != Requirement
Attention != Telemetry
Stake != permission
View != Familiar
View != Report
Omission != absence
```

Do not let Familiar material:

- alter a SPELL declaration;
- satisfy or waive a Requirement;
- fabricate Telemetry;
- establish or prove Presence;
- grant caster or host authority;
- expand Scope;
- raise Cost or Duration ceilings;
- change Technique compatibility;
- reinterpret executor success as proof of Effect;
- change CAST outcome classification.

If a requested action depends on one of those mechanisms, surface the need for the appropriate Environment or Cast mechanism instead of pretending guidance can supply it.

## View handling

When consuming a Familiar View:

1. inspect the exact subject reference (`id`, `caster_id`, `revision`, `digest`);
2. respect the named perspective policy and audience;
3. distinguish included guidance from omitted source material;
4. never reconstruct omitted private material;
5. do not add report-only observations or claims to the View;
6. do not treat the View as evidence that the Familiar was summoned or is Present.

If the exact subject cannot be resolved and verified, the material may still be useful as attributed guidance but must not be represented as an exact Familiar View.

## Corrections

When the practitioner corrects a material dialect, attention, preference, stake, or advisory-authority statement, do not silently evolve the Familiar or View. Treat the correction as candidate source material for Find Familiar or the appropriate view-generation procedure.

A host may adapt presentation transiently during a conversation. Durable Familiar changes require the Familiar's own acceptance and persistence path.
