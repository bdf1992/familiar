# Environment Domain

Environment owns the concrete context in which a cast can be situated: observable state, reachable resources, capabilities, authority mechanisms, scope boundaries, meters, clocks, containment, and other host-provided controls.

Environment is not the Spell declaration and is not the Cast itself. It supplies the concrete mechanisms that let a Cast resolve whether declared Requirements can close and remain governed.

Current evidence for this domain is still distributed through `Situation`, capability receipts, hosts, and casting fixtures. Reassembly should move material here only when it is genuinely environment-generic rather than technique-specific or example-specific.

An Environment may make an operation possible, impossible, observable, bounded, or absent. It does not decide that prose is true merely because a capability is advertised.
