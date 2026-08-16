# Environment Domain

Environment owns the concrete context in which a cast can be situated: observable state, reachable resources, capabilities, authority mechanisms, scope boundaries, meters, clocks, containment, and other host-provided controls.

Environment is not the Spell declaration and is not the Cast itself. It supplies the concrete mechanisms that let a Cast resolve whether declared Requirements can close and remain governed.

Current evidence for this domain is still distributed through `Situation`, capability receipts, hosts, and casting fixtures. Reassembly should move material here only when it is genuinely environment-generic rather than technique-specific or example-specific.

An Environment may make an operation possible, impossible, observable, bounded, or absent. It does not decide that prose is true merely because a capability is advertised.

## Magic runtime

`magic.py` is the 0.6 candidate Environment mechanism for conserved Mana and maintained runtime settings.

Mana is not itself a network. The Environment supplies the shared networked situation through which Mana can be sensed, claimed, committed, spent, drained, and restored. One fixed `total_mana` is conserved while runtime limits bound active participation at network, locality, personal, Cast, commitment, restoration, and level-admission surfaces.

The runtime records legal Mana transitions in a digest-chained ledger and rebuilds current disposition by replay. A restart must not mint usable Mana, erase spent Mana, or silently release claims.

Domains Maintainer is a situated role used when concrete Environment or other domain mechanisms are maintained. Role identity and executor self-report are not maintenance evidence. Restoration requires independently verified evidence and returns eligible Spent Mana to Ambient; it does not award newly created Mana to the Maintainer.

The 0.6 candidate deliberately does not define Level 0 Spells or portable Spell-level semantics. Those remain downstream of the executable runtime substrate.
