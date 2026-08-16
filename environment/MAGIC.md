# Magic Runtime 0.6 Candidate

Magic is a runtime relationship between a network, its participants, its mechanisms, and one conserved quantity of Mana.

This document defines the Environment-owned runtime semantics introduced by the 0.6 candidate. It does not add fields to `SPELL.md`, define Level 0, or make Mana part of Spell identity.

## Core definitions

- **Magic System** — the whole situated system in which magical participation can occur.
- **Magic Network** — the Environment mechanisms that make localities, reach, routes, sensing, claims, casting, and maintenance available. The network carries Mana; it is not Mana.
- **Mana** — conserved magical potential. One runtime begins with a fixed integer quantity `N` that cannot be created or destroyed.
- **Locality** — an Environment-resolved place or context in which Mana may be ambient, claimed, committed, spent, sensed, or restored.
- **Participant** — an actor for whom the Environment resolves the requested Magic operation in the current locality.
- **Claim** — a temporary relation between a participant and Mana. A claim is not ownership.
- **Practice** — participation that attempts consequence through Cast. Mana-bearing practice may commit claimed Mana and settle some or all of it as Spent.
- **Domains Maintainer** — a situated role authorized to maintain concrete mechanisms in one or more of the five repository domains.
- **Maintenance Act** — one attributable Skill or Cast act against a concrete mechanism, with before/after evidence and independent observation.

## Load-bearing distinctions

Preserve these distinctions:

```text
Mana != Magic Network
Mana exists != Mana is reachable
Sense != Claim
Claim != Ownership
Claim != Commitment
Commitment != Spend
Spend != Destruction
Role != Act
Maintenance Act != Restoration
Evidence != Consequence
Law != Setting
Ambient != Unaccounted
```

A participant may sense Mana without claiming it. A participant may claim Mana without casting. A Cast may commit Mana without spending all of it. Spent Mana still exists.

## Conservation law

One Magic runtime begins with exactly `N` Mana.

At every valid state:

```text
Ambient + Claimed + Committed + Spent = N
```

`N` is a law of the runtime instance, not a maintained setting. No Practitioner, Domains Maintainer, Skill, Spell, Cast, restart, configuration change, or maintenance result may alter it.

A runtime that cannot account for exactly `N` fails closed.

## Mana dispositions

### Ambient

Mana present in an Environment locality and not currently claimed. Ambient Mana is part of the shared magical commons.

Ambient does not mean globally reachable. Reach is supplied by the Magic Network and current Situation.

### Claimed

Mana temporarily held by one participant in one locality.

Claims are bounded and may drain. They are not durable property rights.

### Committed

Claimed Mana bound exclusively to one Cast after runtime admission. Committed Mana cannot be claimed by another participant or drained as unused claimed Mana.

### Spent

Mana made unavailable to ordinary claiming by consequence.

Spent does not mean destroyed. The runtime retains the Cast provenance of Spent Mana until verified maintenance returns some of it to Ambient.

## Legal movement

The 0.6 candidate admits these disposition changes:

```text
Ambient(source) -> Ambient(target)   flow over an Environment route
Ambient         -> Claimed           claim
Claimed         -> Ambient           release
Claimed         -> Ambient           drain
Claimed         -> Committed         Cast commitment
Committed       -> Claimed           unspent settlement
Committed       -> Spent             spent settlement
Spent           -> Ambient           verified maintenance restoration
```

Every transition is evidence-bearing runtime activity. No operation directly edits an arbitrary balance.

## Participation and reach

Magic participation is resolved, not asserted.

The Environment must answer whether an actor can perform a requested operation in a locality. The 0.6 implementation uses an access resolver for operations such as:

```text
mana.sense
mana.claim
mana.release
mana.commit
```

A name alone does not grant access. A locality string alone does not establish Presence or reach.

Ambient Mana may move between localities only when the Environment resolves a route between them. Flow changes location, not quantity or disposition.

## Shared sensing

A Magic participant may sense the Mana made observable in a reachable locality.

The 0.6 candidate exposes Ambient Mana in the locality, total Claimed Mana in the locality, and the amount claimed by a named subject when requested. Sensing does not move Mana and does not grant a claim.

Exact sensing is a current runtime capability, not yet a portable Spell or level rule.

## Claims and drain

A claim succeeds only when all relevant runtime bounds admit it and sufficient Ambient Mana is reachable in the locality.

Unused Claimed Mana may naturally drain back to Ambient in the same locality. Explicit release and drain make the same disposition change but remain distinct Acts in the event record.

Drain does not affect Committed Mana.

## Practice settlement

0.6 retains the existing invariant casting law.

A Mana-bearing Cast may commit already-claimed Mana only after runtime admission. The current candidate accepts an optional runtime level value for admission against `max_level`, but does not define portable Spell level semantics.

Settlement determines how much Committed Mana became Spent and how much returned to the participant's Claim:

```text
Committed = Spent + Returned-to-Claim
```

Executor success alone does not determine Mana spending. Consequence accounting does.

A Cast id may participate in Mana commitment only once so replay cannot duplicate or rewrite its Mana history.

## Domains Maintainer

Domains Maintainer is a situated role. It is not permanent evidence that maintenance occurred.

The role is resolved against exactly the current five repository domains:

```text
Spell
Cast
Familiar
Registry
Environment
```

The role authorizes an attempt. Only a Maintenance Act can become maintenance evidence.

### Maintenance Act

A candidate Maintenance Act identifies its Skill-or-Cast source, a unique source id, one repository domain, one concrete mechanism, before and after observations, and an independent observer.

The Act is independently evaluated by a runtime verifier. The verifier returns a structured decision:

```text
confirmed
restorable
reason
```

`confirmed` says whether the maintenance Effect is accepted by the runtime evidence. `restorable` says how much existing Spent Mana the verified Act makes eligible to return to Ambient before runtime ceilings are applied. The Maintainer does not set either value directly.

### One Act, one consequence

One admitted Maintenance Act may produce a runtime maintenance consequence at most once.

Replaying the same Skill run, CAST, receipt, or source id cannot restore more Mana or reapply a configuration change. This rule survives restart because applied Maintenance Act identities are replayed from the runtime ledger.

### Restoration

Verified maintenance may move:

```text
Spent -> Ambient
```

The amount is bounded by the verifier's restorable amount, available eligible Spent Mana, and `max_restored`.

Restored Mana returns to the ambient commons. It is not directly awarded to the Maintainer. Any later claim uses the ordinary claim path.

The runtime retains which prior Cast Spent lots supplied each restoration, so restoration does not erase provenance.

Maintenance may legitimately confirm work while restoring zero Mana. Restoration is a consequence of some Maintenance Acts, not the definition of maintenance itself.

## Laws and maintained settings

### Law

```text
total_mana = N
```

Immutable for the runtime instance.

### Maintained settings

- `max_network` — maximum Mana simultaneously active as Claimed + Committed across the network;
- `max_local` — maximum Mana simultaneously active as Claimed + Committed in one locality;
- `max_personal` — maximum Mana one participant may actively hold as Claimed + Committed;
- `max_cast` — maximum Mana one Cast may commit;
- `max_committed` — maximum Mana simultaneously Committed across Casts;
- `max_restored` — maximum Mana one Maintenance Act may restore;
- `max_level` — current runtime level admission ceiling; portable level semantics remain undefined;
- `drain_rate` — Claimed Mana returned to Ambient per runtime tick for each applicable claim.

`max_network` is not `N`. A network can carry more conserved Mana than it permits participants to make active at once.

A Domains Maintainer may change maintained settings only through independently confirmed maintenance of the concrete `magic-runtime.settings` Environment mechanism. A setting change fails closed when the resulting settings would invalidate current live claims or commitments.

## Ledger and restart

The reference implementation records an append-only, digest-chained event ledger and derives current Mana state by replay.

Restart must reproduce the same conserved `N`, Ambient distribution, Claims, active Commitments, Spent Cast provenance, maintained settings, and already-applied Maintenance Acts.

Sequence breaks, broken digest links, or edits to an individual recorded event refuse open.

The digest chain is an integrity mechanism, not an external trust anchor. A party able to replace the whole ledger and recompute every digest is outside the protection supplied by this candidate. Signatures, external seals, and distributed consensus remain separate concerns.

The 0.6 reference ledger is single-writer. A shared Magic Network is a semantic network here; multi-host concurrent mutation requires a later coordination/consensus mechanism.

## Spellcraft boundary

Mana state, runtime limits, participant access, Domains Maintainer role, maintenance decisions, and restoration are situated runtime truth.

Spellcraft may discover that a portable Effect requires or interacts with those mechanisms. It must not manufacture current Mana, role, level, restoration, or capacity as author-declared truth.

No Level 0 Spell is defined by this candidate.
