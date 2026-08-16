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

### Runtime Obligations

Not every runtime invariant is a capability check, and routing every Requirement through the capability matcher would recreate the operation-name-lookup error one layer up. A capability proves a mechanism exists with sufficient typed capacity. It cannot prove a property of an execution trace, a law over whole-runtime state, or that an implementation realizes its intended Effect.

A Requirement therefore compiles into one or more typed **Runtime Obligations**:

```text
capability gate    an effect path needs a capability with sufficient capacity
state predicate    a before/after condition over resolved state
temporal monitor   a property over an ordered trace, not one instant
global invariant   a law over whole-runtime state, owned by no Technique
semantic trial     behavioural evidence that the intended Effect was realized
provenance proof   evidence carrying attributable observer or signer identity
```

One Requirement may compile to several. A Scope Requirement compiles to a capability gate for the attenuated effect path **and** a post-observation of downstream residuals. Mana conservation compiles to a global invariant and needs no per-Technique capability at all.

Only capability-bearing obligations reach the capability matcher. Everything else binds to a registered discharge mechanism of its own kind. The plan fails closed when a required before or during obligation has no viable path, and when two mechanisms of one kind are both admissible.

Evaluation distinguishes four statuses, because they mean different things:

```text
discharged      evidence was produced and satisfies the obligation
violated        evidence was produced and defeats it
unresolved      no evidence could be produced
not_applicable  the obligation does not apply in this Situation
```

A checker that raises is `unresolved`, never satisfied.

Formal methods are optional mechanisms, not protocol law. A prover, model checker, temporal monitor, policy engine, property suite, or adversarial evaluator may each discharge an obligation when the Environment accepts its evidence contract. **Checker output is evidence, never authority**, so every outcome retains the provenance of whatever produced it — and a candidate cannot supply the trial that promotes itself.
### Concurrency

Two Practitioners may resolve overlapping targets, close against the same pre-state, then execute concurrently. The contract is expressed in terms of **observed pre-state identity** rather than one universal locking strategy, so an Environment that can lock and one that can only compare-and-swap are both conforming.

A CastPlan retains a `StateVersion(resource, version)` per resource it depends on. A resource name alone detects nothing: two Casts naming the same resource conflict only when the version each observed differs from what is there at commit.

```text
reservation   exclusive or shared acquisition before closure
optimistic    execute against isolated state, validate versions at commit
conflict      another consequence invalidated an assumption this Cast required
retry         a NEW attempt with fresh evidence, never a resumed old closure
```

A conflicting commit is refused and **names the resource and both versions**, rather than overwriting another Cast silently. A conflict on any observed resource refuses the whole commit — a partial apply would be the lost update this exists to prevent, wearing a different name.

**Retry is not resumption.** The old closure was against a pre-state that no longer exists, so `replan()` demands a new attempt id and refuses to reuse the old one.

**Deadlock avoidance is by total order, not timeout.** Every multi-resource acquisition sorts by resource name and takes them in that order, so two holders can never each hold what the other needs next. A refused acquisition leaves no partial hold, so nobody waits behind a loser. A timeout would turn a deadlock into a slow deadlock; ordering removes the cycle.

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
