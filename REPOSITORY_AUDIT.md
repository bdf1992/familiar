# Repository Audit

Purpose: make every repository surface legible before architectural change. `AGENTS.md` instructs agents to consult this file first, so a stale audit is itself misleading repository state.

This is an audit, not a claim that every Work artifact is Current doctrine, and not a release.

**Audited commit `f8478df`** — *"Merge pull request #25 from bdf1992/fix/windows-digest-fixture-portability"*, `main`, 107 tracked files.

**Attributable evidence:** `Agent Spells CI` run [31935673778](https://github.com/bdf1992/familiar/actions/runs/31935673778) on `f8478df` concluded **success**. That is the evidence this audit rests on. Saying tests exist is not evidence; a named run against a named commit is.

Lifecycle vocabulary follows `FOUNDATIONS.md`: **Current**, **Work**, **Archive**. Test source is Code; an attributable test run is Evidence.

## How to read a row

| Column | Means |
|---|---|
| Path | Exact repository path. Every tracked file appears exactly once. |
| Purpose | What the surface is for. |
| Stake | Knowledge, Code, or Evidence. |
| Lifecycle | Current, Work, or Archive. |
| Authority / issue | The superseding artifact where one exists, or the GitHub issue that owns a known residual. |

Residuals are **linked, not restated**. Where an issue owns a defect, this file names the issue and says nothing further about the fix. Duplicated backlog prose is how an audit goes stale without anyone noticing.

## Completeness is checked, not asserted

`cast/tests/test_repository_audit_18.py` fails when a tracked file is missing from this inventory, when a path here no longer exists in the tree, or when this file stops naming the commit and CI run it rests on.

It deliberately does **not** check that any row is *correct*. Purpose, Stake, and Lifecycle are judgments no test can make. What it removes is the failure that actually happened: the previous audit predated the 0.6 Magic runtime, the entire Familiar View surface, and every repository governance file, and nothing detected that for two merged pull requests.

## Lifecycle generations

Four generations coexist. **None is archived by this audit.** A newer number is not a supersession, and a lifecycle crossing is an explicit decision that has not been taken for any of these.

```text
0.2 compatibility   Current   the format and Kernel the runtime actually validates against
0.3 candidate       Work      requirement-centered declarations, reached through an adapter
0.4 draft           Work      invariant casting law and the Technique Binding boundary
0.6 draft           Work      Magic participation beneath the existing casting law
```

What that means concretely:

- `spell/format/spell.schema.json` and `cast/kernel/cast.schema.json` are what the running Kernel validates. They are **Current**.
- The 0.3 candidate is exercised in CI through `cast/validation/candidate_adapter.py`, which normalizes a candidate declaration into the compatibility Kernel. It is not a second Kernel.
- The 0.4 draft governs Technique Binding and closure support matching, and is exercised by `cast/validation/casting_04.py`. It has its own CAST schema, which the adapter emits into.
- The 0.6 draft adds Magic participation. Its Environment-owned definition is `environment/MAGIC.md` and its runtime is `environment/magic.py`. **It is not integrated with the Cast lifecycle** — issue #16 owns that crossing, and issue #26 owns whether the Mana state shape changes first.

`AGENT_SPELLS.md` predates the five-domain split and carries historical 0.2 framing. It is **Current/Historical Knowledge**: still referenced, not authoritative where it disagrees with `FOUNDATIONS.md`. Its explicit lifecycle decision remains untaken.

`FIRST_FAMILIAR_SEAL.md` is a bounded readiness statement, frozen as evidence of the state at the first seal. `MIDNIGHT_FIRST_FAMILIAR.md` supersedes its **bootstrap roles** specifically — the first seal got the caster/subject relation wrong, and the correction is that the Agent casts while the human is the subject. The seal is not rewritten; it remains the record of what was true when it was written.

## Root and assembly

| Path | Purpose | Stake | Lifecycle | Authority / issue |
|---|---|---|---|---|
| `README.md` | Practitioner orientation, five-domain map, local-first path, current status. | Knowledge | Current | — |
| `FOUNDATIONS.md` | Constitutional distinctions, SPELL lens, five domains, lifecycle and crossing rules. | Knowledge | Current | Authoritative for domain ownership |
| `AGENTS.md` | Repository participation contract for agents. | Knowledge | Current | — |
| `CLAUDE.md` | Claude-specific adaptation of `AGENTS.md`; creates no separate doctrine. | Knowledge | Current | Defers to `AGENTS.md` |
| `CONTRIBUTING.md` | How repository work is represented as metadata over the five domains. | Knowledge | Current | Defers to `FOUNDATIONS.md` for domain semantics |
| `AGENT_SPELLS.md` | Earlier structural baseline and accumulated protocol reasoning. | Knowledge | Current/Historical | Contains 0.2 framing; supersession decision untaken |
| `REPOSITORY_AUDIT.md` | This inventory. | Knowledge | Current | Completeness checked by `cast/tests/test_repository_audit_18.py` |
| `FIRST_FAMILIAR_SEAL.md` | Bounded pre-cast readiness statement and practitioner procedure. | Knowledge | Current for the seal | Bootstrap roles superseded by `MIDNIGHT_FIRST_FAMILIAR.md` |
| `MIDNIGHT_FIRST_FAMILIAR.md` | Smallest corrected first-cast candidate after the seal exposed a bootstrap-role error. | Knowledge | Current | Supersedes the seal's caster/subject roles only |
| `.gitignore` | Keeps repository-local practitioner data and Python caches out of Git. | Code | Current | — |
| `verify-store.py` | *Untracked.* Not part of this repository. | — | — | — |

Absence of a root `SPELL.md` and `.Binding` is intentional: the repository is not thereby declared a Spell or a registered artifact.

## Repository governance

Added by the work-metadata line and **absent from every previous audit**.

| Path | Purpose | Stake | Lifecycle | Authority / issue |
|---|---|---|---|---|
| `.github/workflows/ci.yml` | Runs the complete `cast/tests` suite. Ubuntu only at this commit. | Code | Current | Windows and symlink-free coverage owned by #17 |
| `.github/workflows/work-metadata.yml` | Triggers work-metadata validation on issues, pull requests, push, and a weekly schedule. | Code | Current | — |
| `.github/scripts/work-metadata.js` | Validates issue and pull-request metadata; maintains the type and priority label taxonomy; applies and removes `invalid`. | Code | Current | — |
| `.github/ISSUE_TEMPLATE/work-item.md` | Work item template carrying the metadata block the validator requires. | Knowledge | Current | — |
| `.github/ISSUE_TEMPLATE/config.yml` | Disables blank issues so every issue carries work metadata. | Code | Current | — |
| `.github/PULL_REQUEST_TEMPLATE.md` | Pull request template: Work, Change, Metadata impact, Validation, Residuals. | Knowledge | Current | — |

**Observation, recorded rather than fixed here:** at this commit the validator holds one open issue as non-conforming. Issue #38 lacks a `## Specification` heading, which `work-metadata.js` requires alongside `## Problem` and `## Acceptance criteria`, and carries the `invalid` label from run [31937193349](https://github.com/bdf1992/familiar/actions/runs/31937193349). The governance mechanism is working; the issue body is what does not conform.

## Spell domain

| Path | Purpose | Stake | Lifecycle | Authority / issue |
|---|---|---|---|---|
| `spell/README.md` | Ownership boundary for declared possibility and Spellcraft. | Knowledge | Current | — |
| `spell/format/SPECIFICATION.md` | Compatibility Spell format specification. | Knowledge | Current | Normative for 0.2 |
| `spell/format/spell.schema.json` | Machine validation for the compatibility Spell format. | Code | Current | What the running Kernel validates against |
| `spell/format/0.3-draft/SPECIFICATION.md` | Requirement-centered candidate format. | Knowledge | Work | — |
| `spell/format/0.3-draft/spell.schema.json` | Generated candidate schema for 0.3 declarations. | Code | Work | Generated from `spell/format/0.3-draft/models.py` |
| `spell/format/0.3-draft/models.py` | Pydantic models defining the 0.3 candidate contract and generating its schema. | Code | Work | Exercised by `cast/tests/test_spell_format_03.py` |
| `spell/format/0.3-draft/examples/find-familiar.SPELL.md` | Candidate-format example declaration. | Knowledge | Work | — |
| `spell/spellcraft/SKILL.md` | Skill for authoring, inspecting, repairing, and migrating Spell declarations. | Code | Current | — |
| `spell/migration/LEDGER.md` | Five-domain reassembly reasoning, ownership findings, unresolved crossings. | Knowledge | Work | Proposes ownership moves not yet taken |
| `spell/migration/agent-skills.md` | Relates Agent Skills to Spell and Technique boundaries. | Knowledge | Work | — |
| `spell/migration/draw-the-owl.md` | Relates Draw the Owl to Familiar and Technique work. | Knowledge | Work | — |
| `spell/migration/mcp.md` | Relates MCP capability surfaces to Cast and Environment. | Knowledge | Work | — |

The active `find-familiar` example uses the 0.3 candidate shape through the adapter while compatibility 0.2 remains present. This coexistence is deliberate Work, not silent equivalence.

## Familiar domain

| Path | Purpose | Stake | Lifecycle | Authority / issue |
|---|---|---|---|---|
| `familiar/README.md` | Ownership and persistence/security boundary. | Knowledge | Current | — |
| `familiar/familiar.schema.json` | Source-of-truth structural contract for a Familiar. | Code | Current | — |
| `familiar/validation.py` | Familiar-owned validator; removes the former reverse dependency on Cast. | Code | Current | — |
| `familiar/store.py` | Exact Familiar persistence; in-memory by default, restart-safe with a local root. | Code | Current | Retains only the latest revision — #15 |
| `familiar/find-familiar/SKILL.md` | Practitioner skill for creating, inspecting, repairing, or validating caster-owned Familiars. | Code | Current | — |
| `familiar/owl/owl.json` | Canonical system Familiar used to advise protocol and Familiar quality. | Knowledge | Current | — |
| `familiar/guidance/SKILL.md` | Applies a Familiar or View as bounded guidance without granting authority or establishing Presence. | Code | Current | Added by PR #9 |
| `familiar/view/README.md` | Familiar View 0.1: a bounded representation of one exact accepted revision. | Knowledge | Current | Added by PR #9 |
| `familiar/view/familiar-view.schema.json` | Machine contract for a Familiar View. | Code | Current | Omission accounting incomplete — #14 |
| `familiar/report/README.md` | Familiar Report: a candidate account *about* a Familiar, deliberately not frozen as a schema. | Knowledge | Work | Added by PR #9 |

A Familiar is guidance identity, not a persona or an authority token. A View represents an accepted revision; a Report is an account about one; neither establishes Presence.

## Registry domain

| Path | Purpose | Stake | Lifecycle | Authority / issue |
|---|---|---|---|---|
| `registry/README.md` | Registry ownership and local-registration security boundary. | Knowledge | Current | — |
| `registry/__init__.py` | Stable public exports for Registry objects and `LocalRegistry`. | Code | Current | — |
| `registry/core.py` | Scroll sealing and verification, Spellbook registration and resolution, Library relations. | Code | Current | Still parses Spell frontmatter privately; ownership move proposed in `spell/migration/LEDGER.md` |
| `registry/local.py` | Restart-safe filesystem adapter for personal Spellbooks. Registration storage, not publication. | Code | Current | — |
| `registry/scroll.schema.json` | Contract for non-executable exact Spell carriers. | Code | Current | — |
| `registry/spellbook.schema.json` | Contract for Spellbook registration metadata. | Code | Current | — |
| `registry/library.schema.json` | Contract for Libraries and their directed relations. | Code | Current | — |

Content addressing gives integrity and exact identity. It does not establish who authored, approved, or published an artifact — #31 owns attestation above digests.

## Environment domain

| Path | Purpose | Stake | Lifecycle | Authority / issue |
|---|---|---|---|---|
| `environment/README.md` | Defines Environment as concrete mechanisms and observations rather than declaration truth. | Knowledge | Current | — |
| `environment/presence/__init__.py` | Public Presence exports. | Code | Current | — |
| `environment/presence/store.py` | Host-owned session Presence store with identity preservation checks. | Code | Current | — |
| `environment/MAGIC.md` | Environment-owned 0.6 Magic runtime semantics: conservation, dispositions, participation, maintenance. | Knowledge | Work | Added by PR #8; **absent from every previous audit** |
| `environment/magic.py` | Conserved Mana runtime with a digest-chained event ledger and restart replay. | Code | Work | Replay guards incomplete — #12; state shape — #26; Cast integration — #16 |

Broader capability receipts still live in `cast/practitioner/situation.py`. `spell/migration/LEDGER.md` proposes eventual Environment ownership; that crossing has not been taken.

## Cast domain — current runtime

| Path | Purpose | Stake | Lifecycle | Authority / issue |
|---|---|---|---|---|
| `cast/README.md` | Ownership boundary for situated casting. | Knowledge | Current | — |
| `cast/kernel/KERNEL.md` | Compatibility Kernel semantics. | Knowledge | Current | — |
| `cast/kernel/spell_kernel.py` | Invariant cast implementation, compatibility validators, runtime hooks. | Code | Current | Scope enforced only at preflight — #10; Authority likewise — #11 |
| `cast/kernel/cast.schema.json` | Compatibility CAST record schema. | Code | Current | — |
| `cast/kernel/__init__.py` | Kernel public exports. | Code | Current | — |
| `cast/practitioner/cast_session.py` | Resumable practitioner preparation state; acceptance gates closure. | Code | Current | — |
| `cast/practitioner/situation.py` | Situation, capability receipt, CastPlan, requirement-to-capability compilation. | Code | Current | Matches on operation name only — #13; ownership split proposed in `spell/migration/LEDGER.md` |
| `cast/practitioner/__init__.py` | Practitioner public exports. | Code | Current | — |

The `cast/familiar`, `cast/format`, and `cast/owl` symlinks are transitional composition aids after the domain move, not duplicate authorities. Runtime resolution currently depends on them materializing as real symlinks, which a checkout with `core.symlinks=false` does not do — #17.

## Cast domain — candidate and draft runtime

| Path | Purpose | Stake | Lifecycle | Authority / issue |
|---|---|---|---|---|
| `cast/kernel/0.3-draft/KERNEL.md` | Earlier candidate casting semantics. | Knowledge | Work | Supersession crossing not formalized |
| `cast/kernel/0.3-draft/cast.schema.json` | Earlier candidate CAST schema. | Code | Work | — |
| `cast/kernel/0.4-draft/CASTING.md` | Requirement-centered casting-law investigation. | Knowledge | Work | — |
| `cast/kernel/0.4-draft/KERNEL.md` | Candidate 0.4 Kernel: binding boundary and closure support matching. | Knowledge | Work | — |
| `cast/kernel/0.4-draft/cast.schema.json` | Candidate 0.4 CAST schema. | Code | Work | Emitted by `cast/validation/casting_04.py` |
| `cast/kernel/0.4-draft/technique-binding.schema.json` | Exact Technique Binding contract. | Code | Work | — |
| `cast/kernel/0.6-draft/KERNEL.md` | Magic participation beneath the existing invariant casting law. | Knowledge | Work | Added by PR #8; **absent from every previous audit**. Cast integration — #16 |

## Cast domain — validation layer

| Path | Purpose | Stake | Lifecycle | Authority / issue |
|---|---|---|---|---|
| `cast/validation/candidate_adapter.py` | Adapts 0.3 candidate declarations into the compatibility Kernel and reconstructs candidate CAST. | Code | Current supporting Work | — |
| `cast/validation/casting_04.py` | Technique Binding closure and support validation around candidate casting. | Code | Current supporting Work | — |
| `cast/validation/candidate/SPELL.md` | Candidate declaration fixture driving requirement-centered tests. | Knowledge | Work | — |
| `cast/validation/candidate/spell.schema.json` | Candidate declaration schema used by the adapter. | Code | Work | — |
| `cast/validation/candidate/cast.schema.json` | Candidate CAST schema used by the adapter. | Code | Work | — |
| `cast/validation/spell-core-shape.md` | Reasoning that shrank the Spell shape. Dated 2026-08-15; explicitly does not change FORMAT 0.2. | Knowledge | Work | — |
| `cast/validation/workspace-tidy-first-cast.md` | Attributable prior filesystem cast observation. | Evidence | Current | — |

## Cast domain — practitioner work documents

| Path | Purpose | Stake | Lifecycle | Authority / issue |
|---|---|---|---|---|
| `cast/work/docs/PRACTITIONER_LOOP_0_5.md` | Summon Owl to Find Familiar to Summon caster Familiar loop, and Draw-the-Owl mapping. | Knowledge | Work | First Find Familiar segment has executable proof |
| `cast/work/docs/REGISTRY_AND_SUMMONING_0_5.md` | 0.5 integration narrative for books, libraries, and Presence. | Knowledge | Work | — |

## Cast domain — examples

| Path | Purpose | Stake | Lifecycle | Authority / issue |
|---|---|---|---|---|
| `cast/examples/find-familiar/SPELL.md` | `find-familiar@0.1.0`; Effect is persistence of one accepted valid Familiar. Acceptance is a before Requirement. | Knowledge | Work | Used by the first-cast proof |
| `cast/examples/find-familiar/binding.json` | Draw-the-Owl Skill Technique Binding realizing `establish`. | Code | Work | — |
| `cast/examples/summon-familiar/SPELL.md` | Establish bounded session Presence of an independently existing Familiar. | Knowledge | Work | — |
| `cast/examples/summon-familiar/SCROLL.json` | Exact non-executable carrier for the Summon Familiar declaration. | Code | Work | — |
| `cast/examples/summon-familiar/binding.json` | Session Presence host binding for Summon Familiar. | Code | Work | — |
| `cast/examples/workspace-tidy/SPELL.md` | Compatibility Spell declaration for workspace-tidy. | Knowledge | Current example | — |
| `cast/examples/workspace-tidy/SPELL.0.3-candidate.md` | Requirement-centered candidate form of the same example. | Knowledge | Work | — |
| `cast/examples/workspace-tidy/SKILL.md` | Ordinary executable Technique used to exercise the casting protocol. | Code | Current example | — |
| `cast/examples/workspace-tidy/technique-binding.0.4-draft.json` | Candidate binding between declaration and implementation. | Code | Work | — |
| `cast/examples/workspace-tidy/host.py` | Integration host: Environment observations and checks plus Cast wiring. | Code | Current example | Intentionally mixed fixture |
| `cast/examples/workspace-tidy/scripts/tidy.py` | Concrete filesystem Technique. | Code | Current example | — |
| `cast/examples/workspace-tidy/CAST.example.json` | Golden CAST record compared exactly by the integration test. | Code | Current example | Shape and regression fixture, not standalone Evidence |

The workspace specimen deliberately does not declare Scope. Its subprocess receives the full workspace path and no runtime mechanism prevents a defective script from reaching other files there. Preservation is checked afterwards, which is detection rather than containment — #10.

## Cast domain — tests and fixtures

All files under `cast/tests/` are **Current Code** because CI depends on them. They are not themselves Evidence; the attributable CI run named at the top of this file is.

| Path | Exercises |
|---|---|
| `cast/tests/fixtures/SPELL.md` | Compatibility Spell fixture. |
| `cast/tests/fixtures/familiar-casual.json` | Familiar dialect and interchangeability fixture. |
| `cast/tests/fixtures/familiar-json.json` | Second dialect fixture, paired with the above. |
| `cast/tests/test_kernel.py` | Compatibility Kernel mechanics: closure, authority refusal, cost, duration, scope bound. |
| `cast/tests/test_candidate_requirements.py` | Requirement-centered candidate behavior through the adapter. |
| `cast/tests/test_casting_04.py` | 0.4 binding and enforcement mechanics. **Carries the Scope containment defect specimen as an `expectedFailure`** — #10. |
| `cast/tests/test_casting_order_04.py` | Invariant casting order; material is consumed only after closure. |
| `cast/tests/test_workspace_tidy_integration.py` | Concrete Skill integration against a real filesystem effect, compared to the golden CAST. |
| `cast/tests/test_workspace_tidy_casting_04.py` | Workspace-tidy through the candidate and binding path. |
| `cast/tests/test_familiar.py` | Familiar validation and guidance invariants. |
| `cast/tests/test_practitioner_05.py` | CastSession, acceptance, FamiliarStore, Situation and CastPlan. |
| `cast/tests/test_presence_05.py` | Session Presence and identity preservation. |
| `cast/tests/test_registry_05.py` | Scroll, Spellbook, and Library exact registration and the non-casting boundary. |
| `cast/tests/test_summon_owl_05.py` | Registered Summon Familiar establishing canonical Owl Presence. |
| `cast/tests/test_local_storage_05.py` | Restart durability and tamper detection for FamiliarStore and LocalRegistry. |
| `cast/tests/test_find_familiar_first_cast_05.py` | End-to-end Find Familiar proof; accepted candidate persists, unaccepted candidate refuses before the executor. |
| `cast/tests/test_spell_format_03.py` | 0.3 candidate Pydantic contract and generated schema agreement. |
| `cast/tests/test_magic_runtime_06.py` | Conserved Mana runtime: conservation, participation, settlement, maintenance, restart replay. **Absent from every previous audit.** |
| `cast/tests/test_repository_audit_18.py` | This file's completeness against the tracked tree. |

**One test is a known-failing specimen by design.** `test_binding_scope_claim_alone_cannot_prove_environment_containment` is marked `@unittest.expectedFailure` and documents a current defect as running code rather than prose. The suite reports `OK (expected failures=1)`. A green suite is therefore **not** a claim that Scope containment holds — #10.

## Normative invariants versus ticket-owned residuals

These are different kinds of statement and the distinction is load-bearing.

**Normative invariants** — properties the protocol asserts, which a conforming runtime must not violate:

- a Spell declares; a Technique Binding realizes; the Kernel decides closure. A binding is not a second declaration.
- refusal precedes effect. Material is not consumed before closure.
- a schema-valid binding can lie. Registration proves presence of a mechanism, never its honesty.
- Mana is conserved: `Ambient + Claimed + Committed + Spent = N`, and no operation edits a balance directly.
- a Familiar is guidance identity, never runtime authority.
- omission is not absence.
- a digest is integrity, not provenance.

**Ticket-owned residuals** — places where the implementation does not yet meet an invariant above. Each is a live GitHub issue and none is restated here:

| Issue | Owns |
|---|---|
| #10 | Scope enforced at the effect path rather than preflight |
| #11 | Authority enforced through an attenuated execution capability |
| #12 | Maintenance replay guarded by source identity and accepted receipt |
| #13 | Requirements bound to exact capability receipts by typed demand |
| #14 | Familiar View omission accounting |
| #15 | Immutable Familiar revisions addressable by `FamiliarRef` |
| #16 | Conserved Mana integrated with the invariant Cast lifecycle |
| #17 | Runtime independence from transitional Git symlinks |
| #18 | This audit |
| #26 | Mana as tensor logic over situated relations |
| #27 | Irreversible external effects and compensating Casts |
| #28 | Ambient reactive blast radius beyond direct capabilities |
| #29 | Semantic alignment evidence for autonomous Spellcraft |
| #30 | Concurrent Cast isolation and conflict semantics |
| #31 | Portable attestation and signer provenance above digests |
| #32 | Requirements compiled into typed runtime obligations |
| #34 · #35 · #36 · #37 · #38 | Milestone 0.7 proof-carrying crossing: closed-plan contract, observation seam, CAST sealing, adversarial conformance suite, and integration |

**Deferred by explicit decision, not by oversight:** remote Library transport and subscription, semantic-version range resolution, Presence lifetimes beyond a session, a Dismiss Spell, Level 0 semantics, portable Mana fields in `SPELL.md`, a universal sandbox implementation, a mandatory theorem prover, external PKI, and distributed consensus.

## What this commit actually proves

`README.md` and this audit must agree, and this section is what they agree on.

**Proven, by the CI run named at the top:** one local practitioner can cast Find Familiar, explicitly accept the resulting Familiar, persist it under a private host path, and resolve the exact artifact after restart. Registration, Presence, and the conserved Mana runtime each pass their own tests. Digest-chained ledger replay reconstructs conserved state across restart.

**Not proven, and not claimed:**

- that Scope or Authority constrain a dishonest Technique's effect path — #10, #11, and the `expectedFailure` specimen says so in running code;
- that the Mana runtime participates in the Cast lifecycle at all — #16;
- that the documented Windows path works — CI is Ubuntu only at this commit, #17;
- that any 0.3, 0.4, or 0.6 draft is Current.
