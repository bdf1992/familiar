# Reassembly Migration Ledger

Status: **Work / Knowledge** on `agent/reassemble-five-domains`.

This ledger applies the five subject domains from `FOUNDATIONS.md` before any physical relocation. `Assembly` below is the repository-root composition surface, **not a sixth domain**. It is used only for artifacts whose subject is the composition itself: root governance, CI, migration work, and true cross-domain integration examples.

## Classification rules

- **Domain** answers who owns the subject: Spell, Cast, Familiar, Registry, Environment, or root Assembly.
- **Stake** answers what role the artifact plays: Knowledge, Code, or Evidence.
- **Lifecycle** answers how it relates to the present: Work, Current, or Archive.
- A test source is Code. A test run is Evidence.
- A synthetic/example CAST is not Evidence merely because it has CAST shape.
- Draft/candidate material remains Work until explicit adoption or retirement. Do not silently call it Archive.
- Cross-domain dependencies do not imply cross-domain ownership. Mark `split` only when one current file genuinely contains subjects owned by different domains.

## Structural findings before moves

1. **`validation/` is not a domain.** It currently mixes Spell Work/Knowledge, Cast Code, and Cast Evidence. Decompose it by owner rather than moving the directory wholesale.
2. **`kernel/spell_kernel.py` owns too much.** It currently loads/validates Spell, Familiar, and CAST schemas. Spell validation belongs to Spell; Familiar validation belongs to Familiar; Cast should consume both and retain CAST validation.
3. **`familiar/store.py` has an inverted dependency.** It imports `validate_familiar` from `kernel.spell_kernel`. Familiar must validate its own artifact and Cast may depend on Familiar, not the reverse.
4. **`practitioner/situation.py` is a real split seam.** `CapabilityReceipt` describes Environment capability; `Situation` and `CastPlan` describe a situated Cast consuming those capabilities.
5. **`presence/store.py` is host/environment state.** The store calls itself host-owned and records whether an identity is present in a context. Environment should own the Presence mechanism/state; Cast owns the summon/release lifecycle that uses it.
6. **`registry/core.py` contains a Spell-specific parsing seam.** Registry may retain Spellbook/Scroll behavior, but Spell frontmatter identity extraction should be supplied by Spell or isolated behind a format-specific adapter rather than making Registry a second Spell parser.
7. **No Commons domain is earned yet.** `migration/`, root CI, and cross-domain examples are Assembly surfaces. Reusable subject matter discovered later with no single owner can reopen the question.
8. **`examples/workspace-tidy/host.py` intentionally mixes an Environment fixture with Cast execution wiring.** Keep it as an integration example for now or split it in place; do not use it as the source of domain APIs.
9. **`examples/workspace-tidy/CAST.example.json` is not Evidence by default.** It is an example/fixture unless tied to an attributable observed run. `validation/workspace-tidy-first-cast.md` is the actual Evidence artifact.

## Root / Assembly

| Current path | Stake | Lifecycle | Proposed destination | Action | References / crossings affected |
|---|---|---:|---|---|---|
| `.github/workflows/ci.yml` | Code | Current | retain | retain | Update test discovery/import paths only after moves. |
| `README.md` | Knowledge | Current | retain | revise after moves | Repository tree and build-order links will change. |
| `FOUNDATIONS.md` | Knowledge | Work | retain | adopt with branch | Becomes Current only through branch adoption. |
| `AGENT_SPELLS.md` | Knowledge | Current | root + archive split | unresolved | Current README still points to it as structural validation / 0.2 baseline. Extract still-current invariants, then explicitly supersede historical baseline before archiving. |
| `migration/LEDGER.md` | Knowledge | Work | retain during migration | retain | This file. Archive only when migration is explicitly closed. |
| `migration/agent-skills.md` | Knowledge | Work | retain during migration | retain | Crosses Spell craft / Technique integration; no Commons needed. |
| `migration/draw-the-owl.md` | Knowledge | Work | retain during migration | retain | Crosses Familiar / Cast practitioner technique. |
| `migration/mcp.md` | Knowledge | Work | retain during migration | retain | Crosses Cast semantic composition and Environment transport/capabilities. |

## Spell

| Current path | Stake | Lifecycle | Proposed destination | Action | References / crossings affected |
|---|---|---:|---|---|---|
| `spell/README.md` | Knowledge | Work | retain | adopt with branch | Ownership surface only. |
| `format/SPECIFICATION.md` | Knowledge | Current | `spell/SPECIFICATION.md` | move | README links; any path-based tooling/docs. |
| `format/spell.schema.json` | Code | Current | `spell/spell.schema.json` | move | `kernel/spell_kernel.py` currently hardcodes `format/spell.schema.json`; extract Spell validator first. |
| `format/0.3-draft/SPECIFICATION.md` | Knowledge | Work | `spell/work/0.3-draft/SPECIFICATION.md` | move | Candidate references only. Do not archive merely because 0.4 Cast work exists. |
| `format/0.3-draft/spell.schema.json` | Code | Work | `spell/work/0.3-draft/spell.schema.json` | move | Candidate tooling/tests if any. |
| `spellcraft/SKILL.md` | Code | Current | `spell/spellcraft/SKILL.md` | move | Documentation paths; no cast-time dependency should be introduced. |
| `validation/spell-core-shape.md` | Knowledge | Work | `spell/work/spell-core-shape.md` | move | Validation docs links only. |
| `validation/candidate/spell.schema.json` | Code | Work | `spell/work/0.3-candidate/spell.schema.json` | move | `validation/candidate_adapter.py`; candidate tests. |
| `validation/candidate/SPELL.md` | Knowledge | Work | `spell/work/0.3-candidate/SPELL.md` or co-located fixture | move | Candidate adapter/tests. |
| `examples/find-familiar/SPELL.md` | Knowledge | Work | retain in assembled example | retain | Logical owner Spell; physical adjacency helps end-to-end example. |
| `examples/summon-familiar/SPELL.md` | Knowledge | Work | retain in assembled example | retain | Logical owner Spell; used by Summon tests. |
| `examples/workspace-tidy/SPELL.md` | Knowledge | Current example | retain in assembled example | retain | Referenced by workspace-tidy integration. |
| `examples/workspace-tidy/SPELL.0.3-candidate.md` | Knowledge | Work | retain in example until candidate closes | retain | Candidate adapter / 0.4 tests. |
| `tests/fixtures/SPELL.md` | Knowledge | Current fixture | `spell/tests/fixtures/SPELL.md` or root integration fixtures | unresolved | Decide whether fixture is Spell-unit or cross-domain. |

### Spell extraction required before Kernel move

Create a Spell-owned loader/validator surface, conceptually:

```text
spell.load(path) -> declaration
spell.validate(declaration)
spell.identity(text|declaration) -> name/version
```

Then Cast and Registry consume it. This removes duplicate/parasitic parsing from `kernel/spell_kernel.py` and `registry/core.py`.

## Cast

| Current path | Stake | Lifecycle | Proposed destination | Action | References / crossings affected |
|---|---|---:|---|---|---|
| `cast/README.md` | Knowledge | Work | retain | revise + adopt | Revise Presence wording after Environment extraction. |
| `kernel/KERNEL.md` | Knowledge | Current | `cast/KERNEL.md` | move | README/docs links. |
| `kernel/spell_kernel.py` | Code | Current | `cast/kernel.py` | **split then move** | Imports from `validation/*`, tests, example host, Familiar store. Extract Spell/Familiar validation first. |
| `kernel/cast.schema.json` | Code | Current | `cast/cast.schema.json` | move | Kernel path constant and validation tests. |
| `kernel/__init__.py` | Code | Current | `cast/__init__.py` | rewrite | Every `kernel.*` import. |
| `kernel/0.4-draft/CASTING.md` | Knowledge | Work | `cast/work/0.4-draft/CASTING.md` | move | Current 0.4 proof docs. |
| `kernel/0.4-draft/KERNEL.md` | Knowledge | Work | `cast/work/0.4-draft/KERNEL.md` | move | Candidate docs. |
| `kernel/0.4-draft/cast.schema.json` | Code | Work | `cast/work/0.4-draft/cast.schema.json` | move | `validation/casting_04.py`. |
| `kernel/0.4-draft/technique-binding.schema.json` | Code | Work | `cast/work/0.4-draft/technique-binding.schema.json` | move | `validation/casting_04.py`, binding fixtures/tests. Technique Binding is Cast-owned. |
| `kernel/0.3-draft/KERNEL.md` | Knowledge | Work | `cast/work/0.3-draft/KERNEL.md` | move; supersession unresolved | Do not call Archive until explicit supersession. |
| `kernel/0.3-draft/cast.schema.json` | Code | Work | `cast/work/0.3-draft/cast.schema.json` | move; supersession unresolved | Same crossing decision as 0.3 draft knowledge. |
| `validation/casting_04.py` | Code | Current validation | `cast/validation/casting_04.py` | move | Imports `kernel.spell_kernel`; tests import it. |
| `validation/candidate_adapter.py` | Code | Current validation | split `spell/` candidate loading from `cast/` candidate casting adapter | split | Currently validates Spell candidate and adapts it into Cast runtime in one file. |
| `validation/candidate/cast.schema.json` | Code | Work | `cast/work/0.3-candidate/cast.schema.json` | move | Candidate adapter. |
| `practitioner/cast_session.py` | Code | Current | `cast/session.py` | move | `tests/test_practitioner_05.py`; practitioner package exports. |
| `practitioner/situation.py` (`Situation`, `CastPlan`, compiler) | Code | Current | `cast/situation.py`, `cast/plan.py` | split | Consume Environment-owned `CapabilityReceipt`; tests/imports. |
| `docs/PRACTITIONER_LOOP_0_5.md` | Knowledge | Work | `cast/work/PRACTITIONER_LOOP_0_5.md` | move | Practitioner loop docs. |
| `examples/find-familiar/binding.json` | Code | Work | retain in example | retain | Logical owner Cast; Technique Binding fixture. |
| `examples/summon-familiar/binding.json` | Code | Work | retain in example | retain | Logical owner Cast; Technique Binding fixture. |
| `examples/workspace-tidy/technique-binding.0.4-draft.json` | Code | Work | retain in example | retain | Logical owner Cast. |
| `examples/workspace-tidy/CAST.example.json` | Knowledge | Current example | retain in example | retain | **Not Evidence unless tied to an attributable run.** |
| `examples/workspace-tidy/SKILL.md` | Code | Current example | retain in example | retain | Technique implementation surface; ordinary Agent Skill remains independently usable. |
| `examples/workspace-tidy/scripts/tidy.py` | Code | Current example | retain in example | retain | Technique implementation. |

## Familiar

| Current path | Stake | Lifecycle | Proposed destination | Action | References / crossings affected |
|---|---|---:|---|---|---|
| `familiar/README.md` | Knowledge | Work | retain | adopt with branch | Ownership surface. |
| `familiar/familiar.schema.json` | Code | Current | retain | retain | Move validator here; Kernel currently points at this path. |
| `familiar/store.py` | Code | Current | retain | **repair dependency** | Replace import from `kernel.spell_kernel` with Familiar-owned validator. |
| `owl/owl.json` | Knowledge | Current | `familiar/owl/owl.json` | move | Tests, practitioner/summon fixtures, docs referencing canonical Owl path. |
| `find-familiar/SKILL.md` | Code | Current | `familiar/find-familiar/SKILL.md` | move | README/docs/skill discovery paths. |
| `tests/fixtures/familiar-casual.json` | Knowledge | Current fixture | `familiar/tests/fixtures/familiar-casual.json` | move | Familiar/kernel tests. |
| `tests/fixtures/familiar-json.json` | Knowledge | Current fixture | `familiar/tests/fixtures/familiar-json.json` | move | Familiar/kernel tests. |

### Familiar extraction required before Cast move

Create a Familiar-owned validator surface and make the store use it. Cast may import Familiar validation at its participant boundary, but Familiar must not import Cast.

## Registry

| Current path | Stake | Lifecycle | Proposed destination | Action | References / crossings affected |
|---|---|---:|---|---|---|
| `registry/README.md` | Knowledge | Work | retain | adopt with branch | Ownership surface. |
| `registry/__init__.py` | Code | Current | retain | retain | Import paths remain stable if registry root remains. |
| `registry/core.py` | Code | Current | retain | split Spell parser seam | Replace private Spell frontmatter parser with Spell identity API or a narrow Spell registration adapter. |
| `registry/library.schema.json` | Code | Current | retain | retain | Registry tests. |
| `registry/scroll.schema.json` | Code | Current | retain | retain | Registry tests/examples. |
| `registry/spellbook.schema.json` | Code | Current | retain | retain | Registry tests. |
| `examples/summon-familiar/SCROLL.json` | Knowledge | Work | retain in assembled example | retain | Logical owner Registry; exact Spell digest couples it to the example declaration. |

## Environment

| Current path | Stake | Lifecycle | Proposed destination | Action | References / crossings affected |
|---|---|---:|---|---|---|
| `environment/README.md` | Knowledge | Work | retain | adopt with branch | Ownership surface. |
| `practitioner/situation.py` (`CapabilityReceipt`) | Code | Current | `environment/capability.py` | split + move | Cast `Situation/CastPlan` should import this rather than define it. |
| `presence/store.py` | Code | Current | `environment/presence.py` | move | `tests/test_presence_05.py`, `tests/test_summon_owl_05.py`, package imports. Cast remains responsible for the operation that establishes/releases Presence. |
| `presence/__init__.py` | Code | Current | fold into `environment/__init__.py` | move/remove | Update `from presence import ...` imports. |
| `examples/workspace-tidy/host.py` | Code | Current example | retain as integration example; optionally split `environment.py` + cast wiring | unresolved | Imports Cast Kernel; contains filesystem observation, authority resolution, requirement checks, and executor wiring. Do not promote wholesale to Environment API. |

Environment should expose concrete capability/observation mechanisms without deciding Spell truth. Cast compiles those mechanisms against declared Requirements.

## Evidence

Evidence is classified by its owning subject domain; it does not need an Evidence directory solely because its stake is Evidence.

| Current path | Domain | Lifecycle | Proposed destination | Action | Notes |
|---|---|---:|---|---|---|
| `validation/workspace-tidy-first-cast.md` | Cast | Current | `cast/evidence/workspace-tidy-first-cast.md` | move | Attributable dated observation of a real filesystem Effect. This is Evidence, unlike the example CAST fixture. |

No stored CI/test-run result artifact is present in the current tree. Test source therefore remains **Code**, not Evidence.

## Tests

Test source is **Code / Current** because CI presently relies on it, even where the subject under test is Work.

| Current path | Logical owner | Proposed destination | Action | Main dependency affected |
|---|---|---|---|---|
| `tests/test_familiar.py` | Familiar | `familiar/tests/test_familiar.py` | move | `kernel.validate_familiar` must become Familiar validator. |
| `tests/test_registry_05.py` | Registry | `registry/tests/test_registry_05.py` | move | Stable registry imports. |
| `tests/test_presence_05.py` | Environment | `environment/tests/test_presence_05.py` | move | `presence` -> `environment.presence`. |
| `tests/test_practitioner_05.py` | Cast | `cast/tests/test_practitioner_05.py` | move | `practitioner.cast_session`, Situation split. |
| `tests/test_kernel.py` | Cast | `cast/tests/test_kernel.py` | move | `kernel` -> `cast`; Spell/Familiar validators extracted. |
| `tests/test_casting_04.py` | Cast | `cast/tests/test_casting_04.py` | move | `validation.casting_04`, kernel imports. |
| `tests/test_casting_order_04.py` | Cast | `cast/tests/test_casting_order_04.py` | move | kernel + candidate adapter imports. |
| `tests/test_candidate_requirements.py` | Cast | `cast/tests/test_candidate_requirements.py` | move | Exercises candidate declaration through Cast adapter; Spell candidate fixture remains Spell Work. |
| `tests/test_summon_owl_05.py` | Assembly integration | `tests/integration/test_summon_owl_05.py` | retain root integration surface | Crosses Registry + Familiar + Environment + Cast. |
| `tests/test_workspace_tidy_casting_04.py` | Assembly integration | `tests/integration/test_workspace_tidy_casting_04.py` | retain root integration surface | Crosses Spell + Cast + example host. |
| `tests/test_workspace_tidy_integration.py` | Assembly integration | `tests/integration/test_workspace_tidy_integration.py` | retain root integration surface | Crosses Cast + Environment + external filesystem Effect. |

Moving unit tests into domains is optional mechanically; the ownership classification is the important part. Root `tests/integration/` is justified because its subject is composition across domains, not shared domain logic.

## Cross-domain Work documents

| Current path | Primary classification | Proposed treatment | Why no Commons yet |
|---|---|---|---|
| `docs/REGISTRY_AND_SUMMONING_0_5.md` | Assembly / Knowledge / Work | split when 0.5 concepts settle: Registry Books section + Cast Summoning section + Environment Presence note; then explicitly supersede original | It is one historical integration narrative spanning owners, not a reusable ownerless subject. |
| `migration/mcp.md` | Assembly / Knowledge / Work | retain during reassembly | MCP is an external substrate crossing Cast and Environment; document is migration reasoning, not a sixth subject domain. |
| `migration/draw-the-owl.md` | Assembly / Knowledge / Work | retain during reassembly | Integration reasoning between Familiar authoring and Cast practitioner technique. |
| `migration/agent-skills.md` | Assembly / Knowledge / Work | retain during reassembly | External-spec migration reasoning. |

## Proposed dependency direction

The reassembly should make dependency direction visible:

```text
Spell -----------┐
Familiar --------┤
Registry --------┼──> Cast
Environment -----┘

Root Assembly composes and tests crossings.
```

This does **not** mean every dependency is one-way forever, but it gives the current runtime a useful default: Cast is the situated composition point and should not own the contracts of the domains it consumes.

Registry may consume a narrow Spell identity surface for Spellbook registration; Environment must not consume Spell semantics merely to advertise capabilities.

## First safe move sequence

Do not bulk-move directories yet. The lowest-risk sequence is:

1. **Extract validators without changing behavior.**
   - Spell owns `load_spell_md`, `validate_spell`, and Spell identity extraction.
   - Familiar owns `validate_familiar`.
   - Cast retains `validate_cast_record`.
2. **Repair dependency inversion.**
   - `familiar/store.py` stops importing Cast.
   - Registry stops privately re-parsing Spell semantics where the Spell identity API suffices.
3. **Split Situation.**
   - Environment owns `CapabilityReceipt`.
   - Cast owns `Situation`, `CastPlan`, and requirement-to-capability compilation.
4. **Move Presence mechanism to Environment.**
   - Preserve behavior and session lifetime tests.
   - Keep Summon semantics and cast lifecycle in Spell/Cast respectively.
5. **Move current Cast kernel surfaces.**
   - `kernel/` current material -> `cast/`.
   - Rewrite imports only after validator extraction.
6. **Move current Spell format surfaces.**
   - `format/` current material -> `spell/`.
   - Candidate/draft material -> explicit `spell/work/` and `cast/work/` surfaces.
7. **Move Familiar-owned Owl and Find Familiar.**
8. **Decompose `validation/` and tests by owner.**
9. **Run full CI and record the run as Evidence if we choose to retain it.**
10. **Explicitly adopt/supersede/archive.** Do not let physical movement imply a lifecycle crossing.

## Open decisions before physical relocation

- Does current `kernel/0.3-draft/` remain active Work, or has 0.4 explicitly superseded it? Record the crossing before Archive.
- Is `AGENT_SPELLS.md` still Current root doctrine, or should its still-live invariants be extracted and its 0.2 material explicitly superseded?
- Should domain unit tests be physically co-located or only logically owned, leaving one root test runner? Either is compatible with the five domains.
- Should `examples/workspace-tidy/host.py` remain deliberately mixed as an integration fixture, or be split into Environment fixture + Cast binding inside the same example?
- When `docs/REGISTRY_AND_SUMMONING_0_5.md` is split, preserve it as Archive only if its historical identity is worth retaining; otherwise explicit retirement may delete it.

No current finding requires a sixth Commons domain.
