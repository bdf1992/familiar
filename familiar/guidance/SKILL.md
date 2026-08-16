---
name: familiar-guidance
description: Apply a valid Familiar or Familiar Report as bounded guidance for representation, attention, preferences, stake, and advisory judgment without granting runtime authority or changing Spell semantics. Use when a host or agent wants to work with a practitioner through an accepted Familiar projection.
---

# Familiar Guidance

Use Familiar material to shape how guidance is represented and what deserves attention while preserving the boundary between advisory configuration and runtime truth.

This is an Agent Skill, not a Spell. It produces no Effect by itself and grants no authority.

## Accepted inputs

Prefer one of:

1. an exact Familiar resolved from a valid `FamiliarRef`; or
2. a Familiar Report whose `subject` identifies an exact Familiar revision and whose projection policy is appropriate for this host or interaction.

When using a report, treat omitted source material as unknown. Do not infer omitted Familiar state from conversation style, history, metadata, or model confidence.

## Apply guidance

A Familiar or report may influence:

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
Report != Familiar
Omission != absence
Claim != observation
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

## Report handling

When consuming a Familiar Report:

1. inspect the exact subject reference (`id`, `caster_id`, `revision`, `digest`);
2. note whether the report says the subject digest was verified;
3. respect the named projection policy and `generated_for` audience;
4. distinguish projected source guidance from report-only observations and claims;
5. preserve claim status such as `asserted`, `supported`, `defeated`, or `unknown`;
6. never reconstruct omitted private material.

A report with `subject_digest_verified: false` may still be useful as attributed advisory material, but it must not be represented as an exact projection of the accepted Familiar.

## Corrections

When the practitioner corrects a material dialect, attention, preference, stake, or advisory-authority statement, do not silently evolve the Familiar or report. Treat the correction as candidate source material for Find Familiar or the appropriate report-generation procedure.

A host may adapt presentation transiently during a conversation. Durable Familiar changes require the Familiar's own acceptance and persistence path.
