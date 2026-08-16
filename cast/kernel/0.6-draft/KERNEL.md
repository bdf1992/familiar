# Agent Spells Kernel 0.6 Draft — Magic Runtime

0.6 adds a conserved Magic runtime beneath the existing casting law. It does not redefine Spell format or introduce Level 0 Spell semantics.

## Conservation law

A Magic network begins with one fixed quantity of Mana, `N`.

```text
Ambient + Claimed + Committed + Spent = N
```

Mana is never created or destroyed. Runtime operations only move existing Mana between dispositions.

## Mana dispositions

- **Ambient** — present in the shared Environment and not currently claimed.
- **Claimed** — temporarily held by a participant.
- **Committed** — reserved to one Cast after the runtime admits that commitment.
- **Spent** — no longer available for ordinary claiming until verified maintenance restores it.

Legal transitions are:

```text
Ambient   -> Claimed      claim
Claimed   -> Ambient      release / drain
Claimed   -> Committed    commit
Committed -> Claimed      unspent settlement
Committed -> Spent        spent settlement
Spent     -> Ambient      verified maintenance
```

A transition that would violate conservation or a maintained runtime limit fails closed.

## Shared sensing

Mana is not the network. The Environment is the networked context through which Mana is present, reachable, sensed, claimed, committed, spent, and restored.

The 0.6 runtime exposes ambient Mana and active claims in a locality. It may also expose how much one subject currently claims. Sensing does not move Mana.

## Claims and drain

A claim is not ownership. It is a temporary relation constrained by network, locality, and personal limits.

Unused claimed Mana may drain back into the same locality's ambient pool. Explicit release and natural drain have the same Mana transition but different event causes.

## Runtime limits

0.6 carries these maintained settings:

- `total_mana` — immutable `N` for the network;
- `max_network` — maximum Mana simultaneously active as claims/commitments;
- `max_local` — maximum active Mana in one locality;
- `max_personal` — maximum one participant may actively claim/commit;
- `max_cast` — maximum Mana one Cast may commit;
- `max_committed` — maximum Mana committed across active Casts;
- `max_restored` — maximum Mana one Maintenance Act may restore;
- `max_level` — runtime admission ceiling only; portable level semantics remain deferred;
- `drain_rate` — claimed Mana returned per runtime tick.

`total_mana` is a conservation constant, not a Maintainer-editable setting. Other settings may be changed only through admitted Domains Maintainer maintenance and may not invalidate live state.

## Practice settlement

0.6 does not add a second casting law.

A Mana-bearing Cast may reserve claimed Mana through `commit` only after the runtime admits the Cast's commitment. Settlement records how much of that commitment became Spent and how much returned to the participant's claim.

Executor success alone does not determine Mana spending. Settlement belongs to runtime consequence accounting.

## Domains Maintainer

`Domains Maintainer` is a situated participation role, not maintenance evidence by itself.

A Maintenance Act must identify a concrete mechanism and provide attributable evidence. The runtime independently verifies that evidence before any Mana transition occurs.

Maintenance may be sourced by a Skill or a Cast. Both use the same restoration path:

```text
Maintenance evidence
    -> role resolved
    -> independent verifier
    -> confirmed restoration
    -> apply max_restored
    -> Spent -> Ambient
```

The Maintainer does not receive the restored Mana directly. Restored Mana returns to the ambient commons and may then be claimed under ordinary limits.

## Ledger

The 0.6 Environment implementation persists an append-only digest-chained event ledger. Current Mana state is a projection of the ledger rather than an independently mutable balance.

Restart must replay to the same conserved disposition. Broken sequence, broken digest chain, or altered event content refuses open.

## Deferred

0.6 intentionally does not define:

- Level 0 Spell semantics;
- Mana fields in `SPELL.md`;
- a portable Spell level schema;
- Prestidigitation or another canonical cantrip;
- real-time clock integration for drain;
- distributed consensus for one Mana ledger across hosts.

Those should be derived from executable runtime evidence rather than authored ahead of it.
