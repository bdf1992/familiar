# Practitioner loop candidate

The next proof is practitioner-facing rather than another schema-only feature.

```text
Summon owl.system
    -> Owl Present
Cast Find Familiar
    -> Draw the Owl preparation loop
    -> practitioner Marks
    -> practitioner accepts Whole
    -> closure
    -> persist exact caster-owned Familiar
    -> FamiliarRef
Cast Summon Familiar(target = FamiliarRef)
    -> caster Familiar Present in the active agent environment
    -> begin comparative agent trials
```

## New runtime shapes

### CastSession

A resumable pre-closure cast state for Techniques that require practitioner interaction. Draft candidates may change through `preparing -> awaiting_mark -> preparing`. Acceptance moves to `ready_to_close`; only then may closure and effectful execution occur.

This preserves the universal law: practitioner drawing is preparation; persistence of the accepted Familiar is the Effect.

### FamiliarStore / FamiliarRef

A FamiliarStore persists an exact schema-valid caster-owned Familiar and returns an immutable reference containing id, caster, revision, and digest. It grants no authority. Spellbooks remain for Spells; FamiliarStore remains for Familiars.

### Situation / CastPlan

Situation is runtime state describing the particular cast: caster, target, current session, environments, present Familiars, observations, and concrete capability receipts. It is not part of `SPELL.md`.

CastPlan binds each Requirement to a concrete mechanism in the Situation. A missing mechanism is a closure gap rather than a prose promise.

Binding is typed mechanism and capacity binding, not operation-name lookup. A Requirement compiles into a `Demand` carrying the required operation, any identity constraints that must hold — capability, protocol, environment, authority, subject, locator — and a named capacity relation with its own parameters. Capacity is not one scalar comparison:

```text
quota        available >= demanded
permissions  granted superset-of required
scope        granted region subset-of resolved admissible region
authority    injected grants subset-of resolved authority
protocol     provided operations superset-of required operations
control      mechanism contains the named execution boundary
```

Note that `scope` and `authority` contain in the opposite direction from `permissions` and `protocol`. A capability that reaches further is not narrower for being larger, and treating every relation as `>=` erases that.

Compilation fails closed three ways rather than guessing: no admissible receipt, more than one admissible receipt where the demand did not supply enough constraints to resolve one exactly, or a demanded narrowing the relation cannot perform. The plan retains the exact selected receipt and the relation evidence per Requirement, so closure evidence can point at the mechanism and the values that decided it.

Where a demand requires narrowing, the plan carries an attenuated handle beside the receipt. A Technique is given the handle, never the broader receipt.

OWL_ENGINE is the intended provider of environment/capability observations. SpellCast consumes those receipts to decide whether this Spell can close in this Situation.

## Draw the Owl mapping

For `find-familiar`:

- Target: a valid caster-owned Familiar.
- Current: the latest complete Familiar candidate.
- Mark: an explicit practitioner correction, rejection, recognition, or acceptance.
- Pass: a revised complete candidate.
- Shapes: early substantive readings the practitioner can recognize or reject.
- Parts: the Familiar contract fields (`dialect`, `attention`, `preferences`, `stake`, `advisory_authority`).
- Features: concrete distinctions within those Parts.
- Whole: schema-valid, explicitly accepted, persistable Familiar artifact.

The system Owl may inspect and advise this drawing when Present. It never becomes the practitioner's Familiar and never changes closure authority.
