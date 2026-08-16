# Draw the Owl -> Find Familiar / Spellcraft

Draw the Owl remains a useful Agent Skill. It is not automatically upgraded into a Spell.

The migration preserves two reusable techniques: produce an inspectable whole rather than stopping at preparation; and preserve the same artifact through feedback using Target / Current / Mark / Pass.

Those techniques are useful to both Find Familiar and Spellcraft, but they are not Agent Spells protocol fields.

The earlier design that made Familiar itself a Spell is retired. Familiar is now a caster-owned artifact. Find Familiar is the Agent Skill that creates/repairs it; Owl is its system Familiar and protocol-aware review aid.

OWL_ENGINE ideas such as persistent state, evidence, and environment observation informed the Kernel, but Owl-specific concepts such as eggs, hatching, shapes/parts/features, strengths/shadows, and form taxonomy are not portable Spell requirements.

The legacy Draw the Owl Skill can remain installable unchanged while Agent Spells develops independently.
