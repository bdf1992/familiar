# Agent Spells — Structural Validation and 0.2 Baseline

Baseline date: 2026-08-15.

This document records the validation that produced the 0.2 baseline. The document is not the protocol implementation; `format/` and `kernel/` remain separate deliverables.

## 1. Format / Kernel separation

The separation is valid, with one correction to the previous repository design.

**FORMAT** is a portable declaration standard for `SPELL.md`. It can be cataloged, parsed, validated structurally, and inspected without an Agent Spells Kernel. It states what effects are claimed and what runtime facts must be available to attempt or confirm those effects. It does not claim that an effect occurred.

**KERNEL** is executable software. It validates a declaration, resolves current telemetry and caster authority, refuses or closes execution, observes what happened, classifies the execution outcome, and emits CAST.

The 0.1 design blurred these layers by putting runtime evaluation, claimed level, energy accounting, evidence, and invocation language inside the portable declaration. Those fields are removed in 0.2.

Agent Skills is the closest format-layer precedent: its specification defines `SKILL.md` frontmatter/body, directory conventions, progressive loading, and format validation. It does not define a standard execution record or postcondition verifier. Source: https://agentskills.io/specification.

MCP is a capability/transport precedent, not the format precedent. The 2026-07-28 MCP revision is stateless at the protocol layer and supports explicit capability discovery, structured tool results/errors, authorization, and explicit handles for durable application state. Agent Spells should compose with those mechanisms rather than replace them. Source: https://modelcontextprotocol.io/specification/2026-07-28 and https://blog.modelcontextprotocol.io/posts/2026-07-28/.

## 2. Structural validation

### Ownership and failure boundaries

| Artifact / component | Owns | Forbids | What breaks if absent |
|---|---|---|---|
| FORMAT | Portable `SPELL.md` field definitions and structural semantics | Runtime state, implementation binding, standing claims | No portable effect contract; each runtime invents its own config |
| KERNEL | Runtime validation, telemetry acquisition, authority resolution, closure, execution observation, outcome classification, CAST emission | Author self-attestation of runtime truth | A declaration can be loaded but not governed or verified |
| SPELL.md | Name/version/description plus declared effects, telemetry, requirements, limits, authority needed | Caster preferences, implementation dependencies, receipts, level/grade | Kernel has no portable statement of what is being attempted |
| CAST | One execution record: participants, closure, observations, outcome, residuals | Changing the declaration after the fact | Downstream systems cannot distinguish attempted, refused, partial, failed, and resolved execution |
| FAMILIAR | One caster's dialect, attention, preferences, stake, and advisory authority ceiling | Granting runtime authority or changing spell semantics | Cast still works, but has no caster-specific guidance layer |
| FIND FAMILIAR | Authoring, repair, inspection, and validation of FAMILIAR artifacts | Casting Spells or granting permissions | Familiars must be hand-authored/validated elsewhere |
| SPELLCRAFT | Authoring, repair, migration, and review of `SPELL.md` | Runtime outcome/standing declaration | Spells can still run, but there is no standard craft workflow for declarations |

### Authority resolution

The **Kernel** owns authority resolution. `SPELL.md` declares authority needed per effect; the host/kernel resolves whether the current caster has it. CAST never accepts a caller-written `satisfied: true` as authority evidence. Familiar authority is an advisory ceiling and cannot widen caster authority.

### Outcome classification

The **Kernel** owns execution outcome classification. An implementation/tool may report success or failure, but the kernel compares that execution with declared postconditions and limits before setting CAST outcome.

### Find Familiar vs Spellcraft validation

They must not duplicate parser/schema logic. The repository owns one SPELL schema and one FAMILIAR schema. Find Familiar validates Familiar against the latter; Spellcraft validates SPELL frontmatter against the former. The Kernel consumes the same validators.

### No Familiar supplied

The cast proceeds with no Familiar. Familiar is an optional guidance/judgment layer. A Spell is invalid if its effect semantics change solely because a different valid Familiar is present.

### Current structural correction: Familiar is not a Spell

The previous `spells/familiar/SPELL.json` conflicts with the validated decomposition. Familiar is an instance artifact; Find Familiar is the Skill that authors/repairs it. Register/recall are persistence operations around the artifact, not evidence that Familiar itself is a Spell.

### CAST is the receipt

The previous separate receipt schema duplicates CAST. In 0.2, CAST is the receipt. There is one durable execution truth.

## 3. Enforced vs asserted

Nothing in this project has been cast against a real external effect under the new 0.2 kernel. No Spell standing is claimed.

| Guarantee | Status | Basis |
|---|---|---|
| `SPELL.md` frontmatter shape validates | Mechanically enforced in reference validator | JSON Schema + semantic reference checks |
| malformed Familiar is rejected when supplied | Mechanically enforced in reference kernel fixture | FAMILIAR schema validation before closure |
| missing/stale declared telemetry prevents closure | Mechanically enforced in reference kernel fixture | observer availability/freshness check |
| missing caster authority prevents closure | Mechanically enforced in reference kernel fixture | host authority resolver result |
| missing/failed `before` requirement prevents closure | Mechanically enforced in reference kernel fixture | checker registry |
| unresolved/violated limit prevents closure | Mechanically enforced in reference kernel fixture | limit checker registry |
| execution result alone proves declared effect | Forbidden by reference kernel | `after` requirements are evaluated separately |
| failed execution still permits post-observation | Mechanically enforced in reference kernel fixture | post-execution telemetry runs after executor error |
| two valid Familiars change guidance but not effect behavior | Mechanically checked only in synthetic fixture | no real host conformance evidence yet |
| description accurately describes implementation | Asserted | format can validate text presence, not semantic truth |
| requirement/limit checker correctly implements its prose description | Asserted until independently tested | kernel can require a checker but cannot infer its correctness |
| authority resolver accurately represents real-world permission | Asserted outside host's own security evidence | kernel consumes resolver decision |
| declared effect corresponds to useful domain outcome | Asserted until cast observations exist | no real cast evidence |
| any level/grade/standing | Asserted / unsupported | no standing evaluator is part of 0.2 baseline |

The reference kernel can mechanically enforce structure around observations; it cannot make the semantic implementation of an observer/checker true by declaration.

## 4. Perception ledger

The 0.1 Familiar declaration contained four effects. The ledger below audits what is observable before reclassification.

| Declared 0.1 effect | Observable today? | What would confirm it | Required change |
|---|---|---|---|
| `summon` | No cast path exists | A structured Familiar candidate/resolution produced from attributable inputs and validated against Familiar schema | Implement as Find Familiar Skill output, not Familiar Spell effect |
| `register` | Partially: registry save/load is unit-tested | Persist Familiar, reload same caster-owned record, verify revision and content | Keep registry behavior outside the Spell effect model |
| `consult` | No reliable effect observation exists | A downstream guidance record while holding underlying Spell behavior constant | Treat as Familiar guidance, not Spell effect |
| `recall` | Partially: registry load is unit-tested | Resolve previously persisted caster Familiar by stable id/revision | Keep as Familiar persistence operation, not Spell effect |

The ledger is the backlog. Unobservable effects are not silently deleted because they are inconvenient; they are either given an observation path or reclassified. Here all four are reclassified because the structural audit shows they belong to Find Familiar/Familiar persistence, not a Spell.

## 5. Revised core requirements

### SPELL.md 0.2 contract

The portable frontmatter contains only:

- `spell_format` — parser/version gate;
- `name` — stable identity for catalogs and CAST;
- `version` — declaration version for record identity;
- `description` — author-asserted catalog description;
- `telemetry` — named observations with optional freshness bounds;
- `limits` — named boundaries for host-provided checkers;
- `effects` — executable claims; each effect references required telemetry, before/after requirements, limits, and caster authority.

Fields removed from 0.1:

- `inherent_ability`: redundant with description plus effects and not independently checkable;
- `magic_words` and invocation: host/user-interface concern;
- `expressions`: absorbed by effects;
- `energy`: concrete resources belong in telemetry and resource ceilings in limits;
- top-level `evidence`: effect confirmation is expressed as `after` requirements and CAST observations;
- `evaluation`, `trials`, `claimed_level`, `grade`, `standing`: execution-derived, never declaration truth;
- `compatibility`: Skill/MCP/host implementation concern, not Spell semantics.

### Kernel 0.2 contract

The kernel must validate SPELL frontmatter/references; resolve the selected effect; validate an optional Familiar; collect declared telemetry; enforce freshness; resolve caster authority through the host; run all `before` requirement and limit checks; refuse closure when any gate is missing/negative; execute only after closure; re-observe telemetry after execution including failure; evaluate `after` requirements and limits; classify outcome as `resolved`, `partial`, or `failed`; and emit one CAST record containing observations and residuals.

The kernel forbids caller-supplied runtime truth from replacing its own observers/checkers/resolvers.

## 6. Migration sort

The current repository contains one pre-existing Agent Skill, and the source Owl repository contains the migration source Skill. No current Skill has earned Spell classification because no Skill has been executed through the new kernel against a real declared effect.

| Skill | Sort | Reason |
|---|---|---|
| `spellcraft` | stays-a-skill | It authors/repairs declarations and is intentionally absent at cast time |
| `draw-the-owl` | stays-a-skill | It remains independently useful completion/revision guidance; some methods can be reused as techniques without reclassifying the whole Skill |
| `find-familiar` (added in 0.2) | stays-a-skill | It authors/repairs a Familiar artifact; it does not require kernel execution |

No on-disk Skill currently sorts cleanly as `spell`, `buff`, or `familiar`. That is a useful result, not a gap to paper over.

The previous `spells/familiar/SPELL.json` fits none of the Skill migration categories because it is not a Skill; it is retired as a misclassified declaration.

A future Skill-to-Spell migration should usually keep the Skill and bind it as a **technique** used by a declared effect. Only runtime records can justify stronger classification.

## 7. Validation plan

The 0.2 reference fixtures are intentionally synthetic. They validate kernel mechanics, not real-world Spell standing.

Runnable suite: `python -m unittest discover -s tests -v` after installing `PyYAML` and `jsonschema`.

1. **`workspace-tidy / closes-and-resolves`** — valid telemetry, authority, before requirement, and limit; kernel closes and postcondition confirms.
2. **`workspace-tidy / authority-denied`** — same declaration, denied `workspace.write`; kernel refuses to close and executor is not called.
3. **`malformed-familiar`** — Familiar missing required dialect; kernel refuses before execution.
4. **`casual-vs-json-familiar`** — human casual Familiar and agent JSON Familiar produce different guidance records while closure, executor result, and outcome remain identical.
5. **`executor-failure`** — kernel closes, executor raises, kernel records failed outcome plus residual and still performs post-observation.
6. **`machine-caster-json-receipt`** — agent caster with JSON Familiar receives a JSON-serializable CAST record.

The next validation step is an actual migrated Skill/MCP implementation with a measurable external effect; until then the tests prove only reference-kernel mechanics.

## 8. Proposal and positioning

### Problem

Agent Skills defines a useful portable format and loading model: `name` and `description` support discovery, the `SKILL.md` body contains unrestricted instructions, resources load progressively, and `skills-ref validate` checks format conventions. The standard does not define a portable declared-effect model, runtime closure decision, post-hoc effect confirmation, partial-vs-complete outcome record, cross-invocation receipt, or composition semantics for two activated Skills. Those behaviors may exist in individual hosts, but they are outside the Agent Skills specification.

That leaves a semantic gap: description-match can select a Skill, but the format itself does not verify that execution behavior matches that description or that the intended downstream effect occurred.

MCP does **not** have the exact deficiencies previously claimed. Current MCP defines structured JSON-RPC protocol errors, tool execution errors (`isError`), structured tool output and optional output schemas, and an authorization model. The actual gap for Agent Spells is higher-level: MCP validates capability calls, not a portable semantic effect spanning one or more calls. A successful MCP tool result is not automatically a verified domain postcondition; MCP also has no Agent-Spells-style standing model or standard for composing several Skills/tools into one declared effect.

### Proposal

Agent Spells adds two separate layers: a portable `SPELL.md` declaration format, parallel in role to Agent Skills format but centered on effect gates and postconditions; and a small Kernel that can wrap Skill/MCP execution, resolve live observations and authority, refuse unsafe/underspecified execution, and emit a machine-consumable CAST record.

Familiar stays outside the effect contract. It is a caster-owned, schema-validated dialect/judgment artifact usable by humans, agents, services, and systems. Swapping Familiars may change guidance representation but not the Spell's declared behavior.

Spellcraft and Find Familiar remain ordinary Agent Skills. They can work without an Agent Spells Kernel. This gives existing Skill ecosystems a migration path instead of requiring replacement.

## Glossary

**Spell** — a capability whose standing is supported by execution records against a portable `SPELL.md` effect declaration; no standing is claimed in this baseline.

**SPELL.md** — portable declaration of named effects and the telemetry, requirements, limits, and authority needed to attempt and confirm them.

**Kernel** — runtime component that validates a SPELL declaration, resolves live gates, observes execution, classifies outcome, and emits CAST.

**CAST** — machine-consumable record of one attempted effect, including closure, observations, outcome, and residuals; CAST is the receipt.

**Caster** — human, agent, service, or system that requests an effect and whose runtime authority is resolved by the host.

**Familiar** — caster-owned dialect and judgment artifact that changes guidance representation/attention without changing Spell semantics or granting authority.

**Find Familiar** — Agent Skill that authors, repairs, and validates Familiar artifacts.

**Spellcraft** — Agent Skill that authors, repairs, migrates, and reviews `SPELL.md` declarations.

**Effect** — declared runtime change or outcome that a Spell implementation attempts and the Kernel can investigate after execution.

**Telemetry** — current host observation required by an effect.

**Limit** — declared boundary that must have an available checker and remain satisfied for an effect to resolve.

**Authority** — runtime permission the host resolves for the caster; never granted by a Familiar or declaration.

**Residual** — declared effect condition left unresolved or unconfirmed after an attempted cast.

**Technique** — Skill/procedure/tool sequence used by an implementation to realize a declared effect.

**Buff** — capability that improves another cast but has no independently declared effect.

**Trick** — capability presented or expected as a Spell whose execution evidence does not support Spell standing; standing rules remain future work.

## Non-goals

- Replace Agent Skills.
- Replace MCP transport, tools, output schemas, errors, or authorization.
- Turn metaphor into runtime semantics.
- Require a Familiar for casting.
- Make Spellcraft part of execution.
- Infer caster identity, preference, or authority from style.
- Declare level, grade, or standing before real execution evidence exists.
- Standardize a universal implementation binding between SPELL and Skill/MCP packages in 0.2.

## Open questions

1. What aggregation rule turns multiple CAST records into `Spell` versus `Trick` standing, and how does standing decrease after later unreliability?
2. How should a host bind a portable effect to one or more Skill/MCP techniques without contaminating the FORMAT with implementation details?
3. How should independent effect checkers be distributed and versioned so a declaration cannot quietly change the meaning of its own postconditions?
4. When several implementations exist, which observations belong to Spell semantics versus technique-specific diagnostics?
5. What minimum real external effect should be the first end-to-end migration fixture?

## Appendix A — Dropped or absorbed structure

The validation intentionally removes earlier structure that did not survive engineering translation.

- **Familiar as a Spell** — dropped. Familiar is a caster artifact; Find Familiar is the Skill that authors it.
- **Separate receipt artifact/schema** — absorbed into CAST.
- **Inherent ability field** — absorbed into description plus declared effects.
- **Expression** — absorbed into effect.
- **Magic words / invocation** — dropped from core protocol; host interface concern.
- **Energy** — dropped from core protocol; observable resources become telemetry and enforceable ceilings become limits.
- **Claimed level / grade / standing in SPELL** — dropped; runtime evidence only.
- **Trials inside SPELL** — dropped; conformance fixtures are external to the portable declaration.
- **Fizzle** — absorbed by closure refusal or failed outcome.
- **Disturbance / wild magic** — absorbed by post-execution observations and residuals; causal interpretation belongs to investigation, not the kernel vocabulary.
- **Casting circle** — absorbed by the concrete closure checks already recorded in CAST.
- **Familiar form/animal taxonomy, strengths/shadows, recognition/history/mutability fields** — dropped from the core Familiar schema. A caster may express such material inside dialect/preferences/attention, but it is not required for interoperable casting.
- **Owl protocol authority** — dropped. Owl is the system Familiar used by Find Familiar/Spellcraft and has no special Kernel privilege.

## Appendix B — Source corrections

The earlier problem framing said MCP tools had "unstructured errors with no authority model." That does not survive source validation and must not be published. MCP supports structured tool/protocol errors and an authorization specification. Agent Spells should claim only the actual gap: no portable cross-call effect contract, no standard postcondition receipt at the semantic effect level, and no standing model across execution history.
