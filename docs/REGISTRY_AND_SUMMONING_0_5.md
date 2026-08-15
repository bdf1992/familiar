# Agent Spells 0.5 Candidate — Books and Summoning

This candidate advances two independent mechanisms and composes them only at the casting boundary.

## 0.5A — Knowledge plane

- A **Scroll** is a non-executable carrier for one exact `SPELL.md` declaration.
- A **Spellbook** registers exact Spell name/version/digest tuples.
- A **Library** registers Spellbooks and directed relations: `issues`, `publishes`, `subscribes_to`, and `consumes_from`.
- Resolution returns an exact declaration plus provenance.
- Registration and resolution must not import or invoke SpellCast execution.

Constitutional boundary: **distribution may change knowledge/addressability; only casting may attempt a declared Effect.**

## 0.5B — Presence plane

`Summon Familiar` attempts one Effect: establish bounded session Presence of an independently existing Familiar.

- Finding/resolving the target happens before closure.
- The target must already exist and validate as a Familiar.
- The Technique establishes Presence only after closure.
- After Requirements independently confirm Presence and identity preservation.
- Session release removes Presence without destroying the underlying Familiar.

Constitutional distinction:

```text
Conjure:  not-exists(X) -> exists(X)
Summon:       exists(X) -> present(X, context)
Dismiss/expiry: present(X, context) -> absent(X, context)
```

`owl.system` is the canonical specimen. Summoning Owl does not make Owl the human caster's Familiar and does not change Owl's system caster record.

## End-to-end proof

1. Seal `summon-familiar@0.1.0` into a Scroll.
2. Register it in a Spellbook.
3. Register the book in a Library and resolve the exact declaration.
4. Confirm no Effect has occurred yet.
5. Cast the resolved Spell against `target.ref = owl.system` using the invariant casting law.
6. Confirm `owl.system` is Present for the session and canonical Owl is unchanged.
7. Release the session and confirm Presence ends while Owl continues to exist.

## Explicitly deferred

- remote library transport and polling;
- signature/trust chains beyond exact digest integrity;
- semantic-version ranges;
- a portable Presence Requirement or Technique Binding mechanism field;
- effect lifetimes other than `session`;
- a `Dismiss` Spell;
- standing/reliability classification.
