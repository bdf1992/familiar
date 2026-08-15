---
name: find-familiar
description: Create, inspect, repair, or validate a caster-owned Familiar artifact for Agent Spells. Use when a human, agent, service, or system needs a durable dialect, attention, preference, stake, and advisory-authority record for use alongside casts. This is an Agent Skill, not a Spell, and it does not grant runtime authority or change Spell behavior.
---

# Find Familiar

Create the smallest valid Familiar that accurately records how this caster wants guidance represented and what it wants attended to.

A Familiar is a caster-authored dialect and judgment layer, not a persona. Build the structured artifact first. Any prose description, icon, metaphor, or presentation is derived from that artifact and does not change the contract.

The Owl at `../owl/owl.json` is the system Familiar used to inspect Familiar quality and protocol boundaries. Owl is protocol-aware because that is its job; ordinary Familiars do not need protocol knowledge. Owl has no special casting authority.

## Familiar contract

A Familiar is unique to a caster and contains only:

- stable Familiar id;
- caster id and kind;
- dialect;
- attention;
- preferences;
- stake;
- advisory authority ceiling.

Validate against `../familiar/familiar.schema.json`.

The schema is the source of truth. Do not add a field because it sounds expressive if it has no casting or guidance consequence.

## Make one

1. Resolve the caster that owns the Familiar. Do not infer a human identity from style or history.
2. Gather caster-authored or explicitly accepted evidence for dialect, attention, preferences, stake, and advisory authority.
3. For machine casters, prefer machine-consumable dialects such as JSON or a supplied schema when useful.
4. Produce the structured candidate before deriving a narrative description of it.
5. Use Owl to inspect the candidate for protocol leakage, unbounded authority, unsupported inference, or persona roleplay.
6. Let the caster or its authorized owner correct the candidate.
7. Validate the final structure before persistence or use.

## Repair one

Repair malformed structure without silently changing the caster. Treat material dialect, stake, preference, or authority changes as caster-authored changes, not autonomous Familiar evolution.

A repair may make the artifact more valid. It may not reinterpret the caster to make the artifact more interesting.

## Boundaries

A Familiar may influence guidance representation, attention, and judgment. It cannot alter a SPELL declaration, satisfy telemetry, grant caster authority, waive requirements or limits, change SpellCast outcome classification, or turn a failed effect into a resolved one.

A cast with no Familiar remains valid unless some separate runtime requirement independently requires one. Any conforming Familiar must be interchangeable at cast time: swapping Familiars may change guidance but not the underlying Spell effect behavior for otherwise identical cast inputs.
