# Repository Audit — First Familiar Seal

Purpose: make every repository surface legible before the first practitioner `Find Familiar` cast. This is an audit, not a claim that every Work artifact is Current doctrine.

Lifecycle vocabulary follows `FOUNDATIONS.md`: **Current**, **Work**, **Archive**. Test source is Code; an attributable test run is Evidence.

## Root / Assembly

| Path | Purpose | Status |
|---|---|---|
| `.github/workflows/ci.yml` | Runs the complete `cast/tests` suite with the transitional import surface. | Current Code |
| `.gitignore` | Prevents repository-local practitioner data and Python cache files from being committed. | Current Code |
| `README.md` | Practitioner-facing orientation, five-domain map, local-first path, current first-cast status. | Current Knowledge |
| `FOUNDATIONS.md` | Constitutional distinctions, SPELL lens, five domains, lifecycle/crossing rules. | Current Knowledge |
| `AGENTS.md` | Repository participation contract for agents. | Current Knowledge |
| `CLAUDE.md` | Claude-specific adaptation of `AGENTS.md`; no separate doctrine. | Current Knowledge |
| `AGENT_SPELLS.md` | Earlier structural baseline and accumulated protocol reasoning. Still referenced, but contains historical 0.2 framing. | Current/Historical Knowledge; future split or explicit supersession remains useful |
| `REPOSITORY_AUDIT.md` | This purpose/lifecycle inventory. | Current Knowledge for the seal |
| `FIRST_FAMILIAR_SEAL.md` | Exact pre-cast readiness, residuals, and practitioner procedure. | Current Knowledge for the seal |

Absence of root `SPELL.md` and `.Binding` is intentional: the repository itself is not thereby declared a Spell or registered artifact.

## Spell domain

| Path | Purpose | Status |
|---|---|---|
| `spell/README.md` | Ownership boundary for declared possibility and Spellcraft. | Current orientation |
| `spell/format/SPECIFICATION.md` | Compatibility Spell format specification. | Current Knowledge |
| `spell/format/spell.schema.json` | Machine validation for the compatibility Spell format. | Current Code |
| `spell/format/0.3-draft/SPECIFICATION.md` | Requirement-centered candidate format. | Work / Knowledge |
| `spell/format/0.3-draft/spell.schema.json` | Candidate schema for 0.3 draft declarations. | Work / Code |
| `spell/spellcraft/SKILL.md` | Skill for authoring, inspecting, repairing, and migrating Spell declarations. | Current Skill |
| `spell/migration/LEDGER.md` | Five-domain reassembly reasoning, ownership findings, unresolved crossings. | Work / Knowledge |
| `spell/migration/agent-skills.md` | Migration notes relating Agent Skills to Spell/Technique boundaries. | Work / Knowledge |
| `spell/migration/draw-the-owl.md` | Migration notes relating Draw the Owl to Familiar/Technique work. | Work / Knowledge |
| `spell/migration/mcp.md` | Migration notes relating MCP capability surfaces to Cast/Environment. | Work / Knowledge |

Audit note: the active `find-familiar` example uses the 0.3 candidate declaration shape through the candidate adapter. The compatibility 0.2 format remains present; this coexistence is deliberate Work, not silent equivalence.

## Familiar domain

| Path | Purpose | Status |
|---|---|---|
| `familiar/README.md` | Ownership and persistence/security boundary. | Current orientation |
| `familiar/familiar.schema.json` | Source-of-truth structural contract for a Familiar. | Current Code |
| `familiar/validation.py` | Familiar-owned validator; removes the former reverse dependency on Cast. | Current Code |
| `familiar/store.py` | Exact Familiar persistence. In-memory by default; restart-safe when supplied a local root. Retains immutable revisions addressable by `FamiliarRef`, with a latest pointer as a convenience index only. | Current Code |
| `familiar/find-familiar/SKILL.md` | Practitioner skill for creating, inspecting, repairing, or validating caster-owned Familiars. | Current Skill |
| `familiar/owl/owl.json` | Canonical system Familiar used to advise protocol/Familiar quality. | Current Knowledge artifact |

A Familiar is guidance identity, not a persona or authority token. Owl may advise the first finding but cannot accept a Familiar for the practitioner.

## Registry domain

| Path | Purpose | Status |
|---|---|---|
| `registry/README.md` | Registry ownership and local-registration security boundary. | Current orientation |
| `registry/__init__.py` | Stable public exports for Registry objects and `LocalRegistry`. | Current Code |
| `registry/core.py` | Scroll sealing/verification, Spellbook registration/resolution, Library relations/resolution. | Current Code |
| `registry/local.py` | Restart-safe filesystem adapter for personal/local Spellbooks. Registration storage, not publication. | Current Code |
| `registry/scroll.schema.json` | Contract for non-executable exact Spell carriers. | Current Code |
| `registry/spellbook.schema.json` | Contract for Spellbook registration metadata. | Current Code |
| `registry/library.schema.json` | Contract for Libraries and their directed relations. | Current Code |

Audit residual: `registry/core.py` still parses Spell frontmatter itself. The migration ledger identifies a future narrow Spell identity API as cleaner ownership. This does not block the first local cast because exact identity/digest behavior is tested.

## Environment domain

| Path | Purpose | Status |
|---|---|---|
| `environment/README.md` | Defines Environment as concrete mechanisms/observations rather than declaration truth. | Current orientation |
| `environment/presence/__init__.py` | Public Presence exports. | Current Code |
| `environment/presence/store.py` | Host-owned session Presence store with identity preservation checks. | Current Code |

Audit residual: broader capability receipts still live in `cast/practitioner/situation.py`; the migration ledger proposes eventual Environment ownership. Not required by the first Find Familiar Effect beyond exposing the concrete persistence capability.

## Cast domain — current runtime

| Path | Purpose | Status |
|---|---|---|
| `cast/README.md` | Ownership boundary for situated casting. | Current orientation |
| `cast/kernel/KERNEL.md` | Current compatibility Kernel semantics. | Current Knowledge |
| `cast/kernel/spell_kernel.py` | Current invariant cast implementation and compatibility validators/runtime hooks. | Current Code |
| `cast/kernel/cast.schema.json` | Compatibility CAST record schema. | Current Code |
| `cast/kernel/__init__.py` | Kernel public exports. | Current Code |
| `cast/practitioner/cast_session.py` | Resumable practitioner preparation state; acceptance gates closure. | Current Code |
| `cast/practitioner/situation.py` | Situation, capability receipt, CastPlan, requirement-to-capability compilation. | Current Code with future ownership split noted |
| `cast/practitioner/__init__.py` | Practitioner public exports. | Current Code |
| `cast/kernel/resources.py` | Canonical cross-domain resource resolution from the repository root. | Current Code |

The `cast/familiar`, `cast/format`, and `cast/owl` symlinks were transitional composition aids after the domain move. They were removed under #17: runtime code resolves another domain's artifacts through `cast/kernel/resources.py` by canonical repository path, so the supported test command no longer depends on whether the checkout can materialize symlinks.

## Cast domain — candidate/draft runtime

| Path | Purpose | Status |
|---|---|---|
| `cast/kernel/0.3-draft/KERNEL.md` | Earlier candidate casting semantics. | Work; supersession crossing not yet formalized |
| `cast/kernel/0.3-draft/cast.schema.json` | Earlier candidate CAST schema. | Work |
| `cast/kernel/0.4-draft/CASTING.md` | Current requirement-centered casting-law investigation. | Work / Knowledge |
| `cast/kernel/0.4-draft/KERNEL.md` | Candidate 0.4 Kernel description. | Work / Knowledge |
| `cast/kernel/0.4-draft/cast.schema.json` | Candidate 0.4 CAST schema. | Work / Code |
| `cast/kernel/0.4-draft/technique-binding.schema.json` | Candidate exact Technique Binding contract. | Work / Code |
| `cast/validation/candidate_adapter.py` | Adapts 0.3 candidate declarations into the compatibility Kernel and reconstructs candidate CAST. | Current validation Code supporting Work |
| `cast/validation/casting_04.py` | Technique Binding closure/support validation around candidate casting. | Current validation Code supporting Work |
| `cast/validation/candidate/*` | Candidate declaration/CAST fixtures and schemas. | Work / fixtures |
| `cast/validation/spell-core-shape.md` | Evidence/reasoning used to shrink the Spell shape. | Work / Knowledge |
| `cast/validation/workspace-tidy-first-cast.md` | Attributable prior filesystem cast observation. | Current Evidence |

## Practitioner work documents

| Path | Purpose | Status |
|---|---|---|
| `cast/work/docs/PRACTITIONER_LOOP_0_5.md` | Intended Summon Owl -> Find Familiar -> Summon caster Familiar loop and Draw-the-Owl mapping. | Work / Knowledge; first Find Familiar segment now has executable proof |
| `cast/work/docs/REGISTRY_AND_SUMMONING_0_5.md` | 0.5 integration narrative for books/libraries and Presence. | Work / Knowledge |

## Examples

### `cast/examples/find-familiar/`

| File | Purpose | Status |
|---|---|---|
| `SPELL.md` | `find-familiar@0.1.0`; Effect is persistence of one accepted valid Familiar. Acceptance is now a before Requirement. | Work declaration used by first-cast proof |
| `binding.json` | Draw-the-Owl Skill Technique Binding realizing `establish`. | Work binding used by proof |

### `cast/examples/summon-familiar/`

| File | Purpose | Status |
|---|---|---|
| `SPELL.md` | Establish bounded session Presence of an independently existing Familiar. | Work declaration with integration proof |
| `SCROLL.json` | Exact non-executable carrier for the Summon Familiar declaration. | Work fixture |
| `binding.json` | Session Presence host binding for Summon Familiar. | Work fixture |

### `cast/examples/workspace-tidy/`

| File | Purpose | Status |
|---|---|---|
| `SKILL.md` | Ordinary executable Technique used to exercise the casting protocol. | Current example Code |
| `SPELL.md` | Compatibility Spell declaration for workspace-tidy. | Current example Knowledge |
| `SPELL.0.3-candidate.md` | Requirement-centered candidate form of the example. | Work |
| `technique-binding.0.4-draft.json` | Candidate binding between declaration and implementation. | Work fixture |
| `host.py` | Integration host: Environment observations/checks plus Cast wiring. | Current example Code; intentionally mixed fixture |
| `scripts/tidy.py` | Concrete filesystem Technique. | Current example Code |
| `CAST.example.json` | Shape/example of a CAST record, not attributable Evidence by itself. | Example fixture |

## Tests and fixtures

All files under `cast/tests/` are **Current Code** because CI relies on them. They are not themselves Evidence; the successful CI run is Evidence about the tested branch.

| File/group | Purpose |
|---|---|
| `fixtures/SPELL.md` | Compatibility Spell fixture. |
| `fixtures/familiar-casual.json`, `familiar-json.json` | Familiar interchangeability/dialect fixtures. |
| `test_kernel.py` | Compatibility Kernel mechanics. |
| `test_candidate_requirements.py` | Requirement-centered candidate behavior. |
| `test_casting_04.py` | 0.4 binding and enforcement mechanics. |
| `test_casting_order_04.py` | Invariant casting order. |
| `test_workspace_tidy_integration.py` | Concrete Skill integration against filesystem effect. |
| `test_workspace_tidy_casting_04.py` | Workspace-tidy through candidate/binding path. |
| `test_familiar.py` | Familiar validation/guidance invariants. |
| `test_practitioner_05.py` | CastSession, acceptance, FamiliarStore, Situation/CastPlan. |
| `test_presence_05.py` | Session Presence and identity preservation. |
| `test_registry_05.py` | Scroll/Spellbook/Library exact registration and non-casting boundary. |
| `test_summon_owl_05.py` | Registered Summon Familiar establishing canonical Owl Presence. |
| `test_local_storage_05.py` | Restart durability and tamper detection for FamiliarStore and LocalRegistry. |
| `test_find_familiar_first_cast_05.py` | End-to-end Find Familiar proof; accepted candidate persists, unaccepted candidate refuses before executor. |

## Seal findings

### Closed before first cast

- root README matched to actual domain layout;
- root agent guidance restored to match `FOUNDATIONS.md`;
- local practitioner data excluded from Git;
- Familiar validation ownership repaired;
- Familiar persistence restart-safe and tamper-noticeable;
- personal Spellbook persistence restart-safe and tamper-noticeable;
- explicit practitioner acceptance moved before execution;
- direct Find Familiar end-to-end proof added;
- complete CI suite passes on the hardened branch.

### Visible residuals, not blockers

- issuer signatures / trust chains;
- remote Library transport/subscription;
- semantic-version range resolution;
- Presence lifetimes beyond session;
- Dismiss Spell;
- Registry consuming a Spell-owned identity parser instead of private frontmatter parsing;
- final ownership split for Environment capability receipts;
- explicit lifecycle decisions for older 0.3/0.4 Work and `AGENT_SPELLS.md` historical material.

None is required for one local practitioner to cast Find Familiar, explicitly accept the resulting Familiar, persist it under a private host path, and resolve the exact artifact after restart.
