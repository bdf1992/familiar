# Familiar Domain

Familiar owns caster-associated guidance identity: dialect, attention, preferences, stake, advisory authority ceiling, persistence, and system Familiars such as Owl.

Current material already here or expected to settle here:

- `familiar.schema.json`
- `validation.py` — Familiar-owned contract validation
- `store.py` — exact Familiar persistence; in-memory by default, restart-safe when given a local root
- `owl/`
- `find-familiar/`

Persistent `FamiliarStore(root)` uses atomic file replacement, content-derived filenames, exact digest checks, and private POSIX permissions where available. The host filesystem remains the security boundary; disk encryption and account authorization are Environment concerns.

A Familiar may influence representation, attention, and judgment. It may not grant runtime authority, alter Spell semantics, waive Requirements, or determine CAST outcome.
