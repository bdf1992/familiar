---
name: find-familiar
description: Create, inspect, repair, or validate a caster-owned Familiar artifact for Agent Spells. Use when a human, agent, service, or system needs a durable dialect, attention, preference, stake, and advisory-authority record for use alongside casts. This is an Agent Skill, not a Spell, and it does not grant runtime authority or change Spell behavior.
---

# Find Familiar

Create the smallest valid Familiar that accurately expresses how this caster wants guidance represented and what it wants attended to.

The Owl at `../familiar/owl.json` is the system Familiar used to help inspect Familiar quality. Owl has no special casting authority.

## Familiar contract
A Familiar is unique to a caster and contains only a stable Familiar id; caster id/kind; dialect; attention; preferences; stake; and an advisory authority ceiling. Validate against `../familiar/familiar.schema.json`.

## Make one
1. Resolve the caster that owns the Familiar. Do not infer a human identity from style or history.
2. Ask for or derive only the dialect, attention, preferences, stake, and advisory authority that available evidence supports.
3. For machine casters, prefer machine-consumable dialects such as JSON or a supplied schema when useful.
4. Produce a candidate artifact and let the caster or its authorized owner correct it.
5. Validate the structure before persistence or use.

## Repair one
Repair malformed structure without silently changing the caster. Treat material dialect, stake, preference, or authority changes as caster-authored changes, not autonomous Familiar evolution.

## Boundaries
A Familiar may influence guidance. It cannot alter a SPELL declaration, satisfy telemetry, grant caster authority, waive requirements/limits, change kernel outcome classification, or turn a failed effect into a resolved one.

Any conforming Familiar must be interchangeable at cast time: swapping Familiars may change guidance representation but not the underlying effect behavior for otherwise identical cast inputs.
