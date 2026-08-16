# Familiar Domain

Familiar owns caster-associated guidance identity: dialect, attention, preferences, stake, advisory authority ceiling, persistence, and system Familiars such as Owl.

Current material already here or expected to settle here:

- `familiar.schema.json`
- `validation.py` — Familiar-owned contract validation
- `store.py` — exact Familiar persistence; in-memory by default, restart-safe when given a local root
- `owl/`
- `find-familiar/`
- `guidance/` — Skill for consuming exact Familiar state or a bounded Familiar View as advisory guidance
- `view/` — source-bounded host/audience representations anchored to an exact `FamiliarRef`
- `report/` — Work describing evidence-backed accounts about Familiars; no frozen report schema yet

Persistent `FamiliarStore(root)` uses atomic file replacement, content-derived filenames, exact digest checks, and private POSIX permissions where available. The host filesystem remains the security boundary; disk encryption and account authorization are Environment concerns.

A Familiar may influence representation, attention, and judgment. It may not grant runtime authority, alter Spell semantics, waive Requirements, or determine CAST outcome.

A Familiar View is derived representation, not Familiar state. It may select, omit, summarize, translate, or rearrange source guidance for a named perspective while remaining anchored to an exact accepted revision. Omitted source material remains unknown to the consumer.

A Familiar Report is conceptually different: it is an account about a Familiar based on attributable knowledge/evidence. Report remains Work until real evidence-backed specimens justify a stable format.
