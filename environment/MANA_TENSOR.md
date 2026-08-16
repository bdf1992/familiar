# Mana Tensor Candidate

Status: Work + Knowledge for issue #26. `environment/MAGIC.md` remains the current 0.6 candidate until an explicit adoption crossing.

## Purpose

Mana is one conserved substance whose situated meaning is relational.

A scalar quantity such as `Cost = 15` is useful for admission and accounting, but it is not a complete description of the Mana participating in a Cast. Two Casts may contract to the same Cost while their Mana differs by Spell component, Caster, Situation, runtime, locality, phase, relation, disposition, or provenance.

```text
ManaTensor(Cast A) != ManaTensor(Cast B)
Cost(Cast A) = 15
Cost(Cast B) = 15
```

The runtime therefore needs both:

- a conserved whole-system magnitude;
- a sparse typed relation describing the makeup and position of that Mana.

## Core law

For one Magic runtime:

```text
TotalMana(M) = N
```

`N` is conserved. Legal Magic operations transform tensor coordinates; they do not create or destroy Mana.

This is the tensor form of the 0.6 conservation law:

```text
Ambient + Claimed + Committed + Spent = N
```

The scalar disposition equation remains a valid projection of the richer state.

## Sparse tensor shape

The candidate reference representation is a set of typed sparse tuples rather than a numerical tensor dependency:

```text
(spell,
 effect,
 component,
 caster,
 situation,
 cast,
 runtime,
 locality,
 phase,
 disposition,
 relation,
 provenance,
 ...) -> amount
```

The axes are runtime relations, not portable `SPELL.md` fields.

Not every axis applies to every Mana relation. Ambient Mana normally has no Spell, Caster, Situation, Cast, or component coordinate. An axis that is **not applicable** is distinct from an axis whose value is **unknown**.

## Cost is a contraction

A Cast's scalar Cost is a deterministic contraction over the Mana related to that Cast:

```text
Cost(cast) = contract(M, cast = cast)
```

The exact production contraction may later narrow by phase/relation/disposition if the runtime evidence requires it. The invariant is that Cost is derived from the tensor rather than maintained as an unrelated balance.

Example:

```text
Cast A — Cost 15
  target-resolution       2
  authority-binding       1
  scope-containment       3
  technique-execution     6
  consequence-evidence    3

Cast B — Cost 15
  target-resolution       1
  material-component      4
  familiar-participation  1
  technique-execution     4
  duration-binding        2
  consequence-evidence    3
```

The scalar is equal. The composition is not.

## Operations

The semantic tensor needs four primitive operations.

### Projection

Select terms by one or more axes without destroying their remaining coordinates.

Examples:

```text
project(M, caster = bdo)
project(M, locality = lab, disposition = ambient)
project(M, cast = cast-7, component = scope-containment)
```

### Contraction

Collapse a projection to a scalar or lower-dimensional summary.

Examples:

```text
Cost(cast-7)
PersonalClaim(bdo)
LocalAmbient(lab)
TotalCommitted()
TotalMana()
```

### Transition

Move/rebind an exact amount from one coordinate relation to another while preserving `N`.

Examples include:

```text
Ambient -> Claimed
Claimed -> Ambient
Claimed -> Committed
Committed -> Claimed
Committed -> Spent
Spent -> Ambient
Ambient(source) -> Ambient(target)
```

The tensor primitive proves exact source availability and conservation. Magic law decides whether the requested transition is admissible.

### Composition

Retain multiple contributing terms for one Cast or relation without flattening them into only a scalar total. Composition is what allows equal-cost Casts to remain distinguishable.

## Spell components

A Spell may declare components/Requirements that participate in an Effect without declaring live Mana allocation.

At Cast time, the Situation and Environment may relate Mana to those components. Therefore:

```text
Spell component identity
        !=
portable Mana amount
```

but:

```text
situated Mana term
        may relate to
Spell component identity
```

This permits runtime evidence such as “3 of this Cast's 15 Mana participated in Scope containment” without making `mana: 3` portable Spell truth.

## Mana is not heterogeneous resource budgeting

Clock time, model tokens, USD, API rate quota, Scope, and Authority remain separate typed Environment capacities.

They can constrain or shape a Mana-bearing Cast. They can also appear in evidence used to determine a Mana relation or Cost. They are not Mana merely because they have magnitudes or vector representations.

```text
Mana != Clock
Mana != Token quota
Mana != Currency
Mana != Rate limit
Mana != Scope
Mana != Authority
```

## Runtime obligations and evidence

The tensor also demonstrates why Requirement enforcement is broader than capability matching.

- Scope attenuation is a capability/control obligation.
- `TotalMana(M) = N` is a global invariant over runtime state.
- a legal sequence such as `Claimed -> Committed -> Spent` is a temporal/transition invariant.
- evidence about which component participated is an attribution/provenance concern.

Issue #32 owns the general Runtime Obligation model. The Mana tensor supplies one state surface those obligations can inspect; it does not turn every Requirement into a Mana relation or capability receipt.

## Reference candidate

`environment/mana_tensor.py` provides the smallest executable candidate:

- `ManaCoordinate` — typed sparse relation coordinates;
- `ManaTerm` — one coordinate plus a positive Mana amount;
- `ManaTensor` — immutable normalized collection with exact conservation;
- `project()` — select relations;
- `contract()` / `cast_cost()` — scalar contraction;
- `transition()` — conservation-preserving rebinding;
- `composition()` — canonical inspectable makeup.

It is intentionally not integrated into `MagicRuntime` yet. Integration belongs after the tuple axes and transition semantics survive tests and review, so #16 does not harden an unstable representation.
