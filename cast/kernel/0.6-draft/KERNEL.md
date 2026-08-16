# Agent Spells Kernel 0.6 Draft — Magic Participation

0.6 adds Magic participation beneath the existing invariant casting law. The Environment-owned definition is `../../../environment/MAGIC.md`.

It does not change the 0.3 Spell format and does not define Level 0 Spell semantics.

## Kernel responsibility

The Kernel does not own Mana as a substance or topology. It coordinates Cast participation with Environment mechanisms that expose Mana access and accounting.

For a Mana-bearing Cast, the relevant runtime sequence is:

```text
resolve invocation / actor / target / Technique
        ↓
resolve Situation and Environment capabilities
        ↓
evaluate ordinary before Requirements
        ↓
resolve Mana access + sufficient Claim
        ↓
closure
        ↓
Claimed -> Committed
        ↓
govern effectful execution
        ↓
Environment observes consequence
        ↓
Environment consequence decision / receipt
        ↓
settle Committed -> Spent + Claimed
        ↓
ordinary after Requirements / outcome / residuals
        ↓
CAST
```

A refusal before commitment does not spend Mana.

Commitment does not itself prove consequence. Settlement is closed by an Environment consequence verifier: the caller does not choose `spent` directly. A confirmed decision identifies an independent observer and receipt and determines how much Committed Mana became Spent.

## Conservation dependency

The Kernel may request legal Mana transitions, but the Environment Magic runtime must preserve:

```text
Ambient + Claimed + Committed + Spent = N
```

The Kernel cannot mint, destroy, directly edit, or self-restore Mana.

## Level admission

The current runtime can reject a supplied runtime level above `max_level`.

That is only an admission mechanism. 0.6 does not establish how a Spell receives a level, what Level 0 means, how Mana cost maps to level, or whether level belongs in a future portable Spell declaration. Those require later executable evidence.

## Maintenance participation

Domains Maintainer is a situated role resolved against one of the existing five domains.

Maintenance may originate in a Skill or a Cast. Both produce candidate Maintenance Evidence and use the same Environment verification path.

The candidate evidence does not certify its own observer. The Environment verifier returns the accepted observation identity and receipt together with `confirmed` and `restorable`; self-observed decisions refuse.

The Kernel does not treat role possession, executor success, prose, caller-supplied observer names, or a repeated receipt as restoration evidence.

A confirmed Maintenance Act is recorded exactly once even when it restores zero Mana. Restoration is one possible consequence of maintenance, not the identity of the Maintenance Act. When restoration is available, the Environment applies `max_restored`, preserves Spent-Cast provenance, and returns restored Mana to Ambient.

## Runtime settings

`total_mana = N` is a law and is not configurable.

The Environment owns maintained ceilings for network activity, locality activity, personal claims, per-Cast commitment, total commitment, restoration, level admission, and drain.

Changing those settings is itself maintenance of the Environment mechanism `magic-runtime.settings` and must be independently confirmed.

## Consequence-boundary questions for 0.6

Every Mana-bearing integration should answer:

1. Who resolved that the actor may sense/claim/commit in this locality?
2. Which reachable Ambient Mana is being claimed?
3. At what exact closure edge does Claimed become Committed?
4. Which Environment observation and receipt determine Committed -> Spent?
5. Which unused commitment returns to Claim?
6. Can a caller assert its own spend result?
7. Can a failed/refused Cast accidentally spend or duplicate Mana?
8. Can the Cast id be replayed?
9. Can maintenance evidence be replayed?
10. What concrete mechanism was maintained?
11. Which independent verifier observation supports the Maintenance Act?
12. Is the Act recorded even when restoration is zero?
13. Which prior Spent Cast provenance supplied any restored Mana?
14. Does every transition preserve N?
15. Can any caller mutate already-hashed event material?

## Reference implementation

`environment/magic.py` currently supplies a single-writer reference runtime with:

- access resolution for sensing, claiming, releasing, and committing;
- Environment route resolution for Ambient flow between localities;
- conserved Mana dispositions;
- deterministic drain;
- per-Cast commitment and verifier-closed settlement;
- attributable Spent lots;
- one-use Maintenance Acts, including confirmed zero-restoration Acts;
- structured maintenance decisions with verifier-resolved observer and receipt identity;
- Domains Maintainer runtime-setting maintenance;
- caller-detached digest-bearing event material;
- append-only digest-chained persistence and exact replay;
- strict integer validation that excludes Python booleans from Mana and limit quantities.

The reference implementation is evidence for the semantics, not a claim that one storage implementation is the only valid Technique.

## Deferred

0.6 intentionally leaves these beyond its boundary:

- Level 0 Spell semantics;
- Mana fields in `SPELL.md`;
- portable Spell level semantics;
- Prestidigitation/cantrip specimens;
- wall-clock scheduling for drain;
- external signatures/seals for the Mana ledger;
- multi-host consensus/concurrent mutation.
