# Repository Audit

Purpose: make every repository surface legible before architectural change. `AGENTS.md` instructs agents to consult this file first, so a stale audit is itself misleading repository state.

This is an audit, not a claim that every Work artifact is Current doctrine, and not a release.

**Audited commit `c9f34e52087a0118303b92e04966c716ac2bc1cd`** — *"Merge PR #72: attach evidenced Situation to open CrossingPlan"*, `main`.

**Attributable evidence:** `Agent Spells CI` run [31980922205](https://github.com/bdf1992/familiar/actions/runs/31980922205) on `812340530d8498eaabe5e5f6d01f8fdde9845370` concluded **success**, running **371 tests, OK** across ubuntu-latest, windows-latest, and a symlink-disabled checkout before merge as PR #72. Work Metadata run [31980922200](https://github.com/bdf1992/familiar/actions/runs/31980922200) also concluded **success**. That is the evidence this audit rests on. Saying tests exist is not evidence; a named run against a named commit is.

The commit that merges any change to this file is necessarily one commit later than the one it names. That is not drift: the completeness check covers the tree mechanically on every run, and the named run covers the behavior at a commit that actually existed.

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

Five generations coexist. **None is archived by this audit, and none has ever been adopted.** A newer number is not a supersession. `FOUNDATIONS.md` is explicit that *"Work becomes Current only through explicit adoption"*, and **no such crossing has been recorded for any generation here.**

```text
0.2 compatibility   Current   the format and Kernel the runtime actually validates against
0.3 candidate       Work      requirement-centered declarations, reached through an adapter
0.4 draft           Work      invariant casting law and the Technique Binding boundary
0.5 work docs       Work      practitioner loop and registry/summoning narratives — no kernel generation
0.6 draft           Work      Magic participation beneath the existing casting law
```

**Read that table as parallel drafts beside a Current 0.2, not as a ladder that has been climbed.** 0.6 does not build on 0.5; it builds on the 0.3 format and the existing casting law and skips 0.5 entirely, which is coherent once you notice 0.5 was never a kernel generation. `spell/format/0.3-draft/SPECIFICATION.md` still says so in its own header: *"FORMAT 0.2 remains Current until an explicit adoption crossing."*

### Recorded standing

Under #53, each generation now carries exactly one disposition. The available dispositions are those `FOUNDATIONS.md` already defines — **adopted**, **superseded**, **retired**, **retained** — and no new vocabulary is introduced.

**Every generation is `retained` as Work.** Nothing is adopted, superseded, retired, or archived by this record. That is not a deferral: it is what the material itself says, and the evidence is in the documents rather than in anyone's memory.

| Generation | Artifacts | Disposition | Why |
|---|---|---|---|
| 0.3 format | `spell/format/0.3-draft/SPECIFICATION.md`, `spell/format/0.3-draft/spell.schema.json`, `spell/format/0.3-draft/models.py`, `spell/format/0.3-draft/examples/find-familiar.SPELL.md` | **retained** | Its own header states *"FORMAT 0.2 remains Current until an explicit adoption crossing."* No adoption has occurred, so 0.2 remains Current and this remains the candidate. |
| 0.3 kernel | `cast/kernel/0.3-draft/KERNEL.md`, `cast/kernel/0.3-draft/cast.schema.json` | **retained** | Its own header states it *"does not replace the current reference Kernel yet."* Not superseded — see the ledger answer below. |
| 0.4 | `cast/kernel/0.4-draft/CASTING.md`, `cast/kernel/0.4-draft/KERNEL.md`, `cast/kernel/0.4-draft/cast.schema.json`, `cast/kernel/0.4-draft/technique-binding.schema.json` | **retained** | Declares itself *"a development draft"* that *"extends the requirement-centered 0.3 work"* and *"does not establish Spell standing."* Extension is not replacement. |
| 0.5 | `cast/work/docs/PRACTITIONER_LOOP_0_5.md`, `cast/work/docs/REGISTRY_AND_SUMMONING_0_5.md` | **retained** | Practitioner and registry integration narrative. **There is no 0.5 kernel generation**, so there is nothing here that could be adopted as a runtime specification. |
| 0.6 | `cast/kernel/0.6-draft/KERNEL.md`, `environment/MAGIC.md`, `environment/magic.py` | **retained** | Declares that it *"adds Magic participation beneath the existing invariant casting law"* and *"does not change the 0.3 Spell format."* It is not integrated with the Cast lifecycle at all — #16 owns that crossing. |

**The ledger's open question is answered.** `spell/migration/LEDGER.md` asks whether the 0.3 kernel draft remains active Work or has been explicitly superseded by 0.4. (It asks this using the pre-reassembly relative path, which is why the path is not cited here: `cast/kernel/0.3-draft/` is where that material actually lives.) It remains active Work. 0.4 states in its own header that it **extends** the 0.3 work, and `cast/kernel/0.4-draft/CASTING.md` describes itself as *"derived from the 0.3 FORMAT/KERNEL validation work."* Derivation and extension are not supersession. Nothing archives 0.3, and no crossing is recorded because none occurred.

**Read the generations as layers, not as a ladder.** Each one explicitly declines to replace what came before: 0.4 extends 0.3, 0.6 sits *beneath* the casting law 0.4 describes and preserves the 0.3 format, and 0.5 is not a kernel generation at all. That is why no supersession can be recorded — not because the decision is being avoided, but because every document in the chain says it is additive.

### The generations and the running code

**The code never forked.** There is one `cast/kernel/spell_kernel.py`, still titled for the 0.2 compatibility Kernel, and every merged correctness and architecture change lands in it. What runs is best described this way:

- `spell/format/spell.schema.json` and `cast/kernel/cast.schema.json` are what the Kernel actually validates against. They are **Current**, and they are 0.2.
- The 0.3 candidate reaches that Kernel through `cast/validation/candidate_adapter.py`, which normalizes a candidate declaration into the compatibility shape. It is an adapter, not a second Kernel.
- The 0.4 casting law and Technique Binding boundary are implemented and exercised — `cast/validation/casting_04.py`, `cast/tests/test_casting_04.py`, `cast/tests/test_casting_order_04.py` — and the adapter emits into 0.4's CAST schema.
- The 0.6 Magic runtime exists and passes its own tests, but no Cast reaches it. `cast/kernel/spell_kernel.py` contains no Mana participation; #16 owns that.

**So the running Kernel implements substantial parts of 0.3, 0.4, and 0.6 while none of those drafts is its specification.** The implementation ran ahead of the lifecycle record. A reader asking *"which generation governs this code?"* gets the honest answer: **0.2 is the only Current specification, and the code exceeds it.** Closing that gap means either adopting a generation as the Kernel's specification or writing a specification that describes what the Kernel now does — and both are lifecycle crossings that require an explicit decision. This record does not take one.

That decision is not owned by this section. Recording the standing is what #53 required, and silence is what it forbade.

**The route out is specified in `LIFECYCLE_LADDER.md`.** It states the ordered crossings from 0.2 Current to 0.7 Current — schema reconciliation (#55), FORMAT 0.3 (#56), KERNEL 0.4 (#57), the 0.5 disposition (#59), 0.6 Magic participation (#58), then 0.7 (#38) — with entry conditions and required evidence for each. It takes none of them. **Until a rung is actually taken, the standing recorded in this section remains authoritative**, and a route is not a promotion.

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
| `LIFECYCLE_LADDER.md` | The ordered sequence of crossings from 0.2 Current to 0.7 Current, with an owning issue per rung. | Knowledge | Work | Specifies a route, not a standing. Takes no crossing — #55, #56, #57, #58, #59 and #38 own the rungs |
| `FIRST_FAMILIAR_SEAL.md` | Bounded pre-cast readiness statement and practitioner procedure. | Knowledge | Current for the seal | Bootstrap roles superseded by `MIDNIGHT_FIRST_FAMILIAR.md` |
| `MIDNIGHT_FIRST_FAMILIAR.md` | Smallest corrected first-cast candidate after the seal exposed a bootstrap-role error. | Knowledge | Current | Supersedes the seal's caster/subject roles only |
| `.gitattributes` | Pins every tracked file to LF in the repository and in the working tree. | Code | Current | Digest identity rests on bytes; unmanaged line endings put a platform variable under every seal |
| `.gitignore` | Keeps repository-local practitioner data and Python caches out of Git. | Code | Current | — |
| `verify-store.py` | *Untracked.* Not part of this repository. | — | — | — |

Absence of a root `SPELL.md` and `.Binding` is intentional: the repository is not thereby declared a Spell or a registered artifact.

## Repository governance

Added by the work-metadata line and **absent from every previous audit**.

| Path | Purpose | Stake | Lifecycle | Authority / issue |
|---|---|---|---|---|
| `.github/workflows/ci.yml` | Runs the complete `cast/tests` suite across ubuntu-latest, windows-latest, and a checkout with `core.symlinks=false`. | Code | Current | Matrix added by #39; #17 closed |
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
| `spell/alignment.py` | Effect invariants, semantic trials carrying evaluator provenance, and fail-closed promotion for autonomous Spellcraft. | Code | Current | Added by #51 (issue #29). Evidence never confers authority: a candidate cannot supply the trial that promotes itself |
| `spell/migration/LEDGER.md` | Five-domain reassembly reasoning, ownership findings, unresolved crossings. | Knowledge | Work | Proposes ownership moves not yet taken. Its 0.3-versus-0.4 question is answered and struck under #53; the remaining open decisions stand |
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
| `familiar/store.py` | Exact Familiar persistence; in-memory by default, restart-safe with a local root. Retains immutable revisions addressable by `FamiliarRef`; the latest pointer is a convenience index only. | Code | Current | #15 closed by #40 |
| `familiar/find-familiar/SKILL.md` | Practitioner skill for creating, inspecting, repairing, or validating caster-owned Familiars. | Code | Current | — |
| `familiar/owl/owl.json` | Canonical system Familiar used to advise protocol and Familiar quality. | Knowledge | Current | — |
| `familiar/guidance/SKILL.md` | Applies a Familiar or View as bounded guidance without granting authority or establishing Presence. | Code | Current | Added by PR #9 |
| `familiar/view/README.md` | Familiar View 0.1: a bounded representation of one exact accepted revision. | Knowledge | Current | Added by PR #9 |
| `familiar/view/__init__.py` | Public View exports. | Code | Current | — |
| `familiar/view/familiar-view.schema.json` | Machine contract for a Familiar View. Accounts for every source guidance category exactly once. | Code | Current | #14 closed by #42 |
| `familiar/view/builder.py` | Builds a View from a store-resolved `FamiliarRef` and validates omission accounting. | Code | Current | Added by #42 |
| `familiar/report/README.md` | Familiar Report: a candidate account *about* a Familiar, deliberately not frozen as a schema. | Knowledge | Work | Added by PR #9 |
| `familiar/domain_handle/README.md` | Bounded Work description for Context + Domain Familiarity + optional Subject Familiar resolution. | Knowledge | Work | #67 |
| `familiar/domain_handle/__init__.py` | Work exports for the read-only Domain Handle resolver. | Code | Work | #67 |
| `familiar/domain_handle/resolver.py` | Read-only non-flattening resolver; preserves source identities, disagreement and unknowns while exposing no effectful path. | Code | Work | #67 |
| `familiar/domain_handle/fixtures/context.json` | Machine-readable repository Context Work specimen anchored to the #66 survey commit. | Knowledge | Work | #67; derived from #66 |
| `familiar/domain_handle/fixtures/domain-familiarity.json` | Machine-readable learned Domain Familiarity Work specimen, explicitly distinct from Subject Familiar. | Knowledge | Work | #67; derived from #66 |

A Familiar is guidance identity, not a persona or an authority token. A View represents an accepted revision; a Report is an account about one; neither establishes Presence. Domain Familiarity remains separate Work from a Subject Familiar and cannot grant runtime authority.

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
| `registry/attestation.py` | Optional attestation envelope above content digests, one local/offline signing path, and consumer-local trust policy. | Code | Current | Added by #50 (issue #31). A digest proves the bytes; only an attestation names who vouched for them, and trust remains the consumer's |

Content addressing gives integrity and exact identity. It does not establish who authored, approved, or published an artifact — #31 owns attestation above digests.

## Environment domain

| Path | Purpose | Stake | Lifecycle | Authority / issue |
|---|---|---|---|---|
| `environment/README.md` | Defines Environment as concrete mechanisms and observations rather than declaration truth. | Knowledge | Current | — |
| `environment/presence/__init__.py` | Public Presence exports. | Code | Current | — |
| `environment/presence/store.py` | Host-owned session Presence store with identity preservation checks. | Code | Current | — |
| `environment/MAGIC.md` | Environment-owned 0.6 Magic runtime semantics: conservation, dispositions, participation, maintenance. | Knowledge | Work | Added by PR #8; **absent from every previous audit**. Retained as Work under #53 — see § *Lifecycle generations* |
| `environment/magic.py` | Conserved Mana runtime with a digest-chained event ledger and restart replay. | Code | Work | Replay guards closed by #41. State shape — #26; Cast integration — #16 |
| `environment/MANA_TENSOR.md` | Candidate boundary for Mana as typed sparse relations over situated Spell participation. | Knowledge | Work | Added by #33 (issue #26). Explicitly a candidate: it does not replace `MAGIC.md` and is not integrated into `MagicRuntime` |
| `environment/mana_tensor.py` | Immutable sparse `ManaCoordinate` / `ManaTerm` / `ManaTensor`, projection, contraction, and conservation-preserving transitions. | Code | Work | State shape remains open design work — #26 |
| `environment/scope.py` | Environment-owned effect-path boundaries for Scope enforcement, plus one reference filtered object capability. | Code | Current | Added by #44 (issue #10). The Kernel specifies the contract; the Environment owns the mechanism |
| `environment/authority.py` | Attenuated credentials for Authority enforcement, plus one reference host credential. | Code | Current | Added by #45 (issue #11) |
| `environment/consequence.py` | Consequence classification for irreversible external effects, and compensation as a separate attributable record. | Code | Current | Added by #48 (issue #27) |
| `environment/blast_radius.py` | Direct, declared, observed and unknown reactive reach; reactive dependency graph and downstream observation. | Code | Current | Added by #52 (issue #28). A narrow handle is not evidence of a small radius |

Broader capability receipts still live in `cast/practitioner/situation.py`. `spell/migration/LEDGER.md` proposes eventual Environment ownership; that crossing has not been taken.

## Cast domain — current runtime

| Path | Purpose | Stake | Lifecycle | Authority / issue |
|---|---|---|---|---|
| `cast/README.md` | Ownership boundary for situated casting. | Knowledge | Current | — |
| `cast/kernel/KERNEL.md` | Compatibility Kernel semantics. | Knowledge | Current | — |
| `cast/kernel/spell_kernel.py` | Invariant cast implementation, compatibility validators, runtime hooks. Scope and Authority now bind the effect path through Environment-owned boundaries; consequence, compensation, and reactive reach are read from the Environment rather than from the Technique's account of itself. | Code | Current | #10, #11, #27, #28 closed. Titled 0.2 but carrying every generation's work — see § *Lifecycle generations* and #53 |
| `cast/kernel/cast.schema.json` | Compatibility CAST record schema. | Code | Current | 0.7 sealing contract owned by #36 |
| `cast/kernel/resources.py` | Canonical cross-domain resource resolution from the repository root. | Code | Current | Added by #39 (issue #17), replacing the composition symlinks |
| `cast/kernel/__init__.py` | Kernel public exports. | Code | Current | — |
| `cast/practitioner/cast_session.py` | Resumable practitioner preparation state; acceptance gates closure. | Code | Current | — |
| `cast/practitioner/situation.py` | Situation, capability receipt, typed Requirement demand, capacity relations, attenuation, CastPlan, requirement-to-capability compilation. | Code | Current | #13 closed by #43. Ownership split still proposed in `spell/migration/LEDGER.md` |
| `cast/practitioner/handle_situation.py` | Read-only HandleView-to-Situation evidence seam; verifies Handle source identity, compares charted claims with attributable Environment observations, records exact Demand/receipt/attenuated-handle matches, and derives an integrity digest over authoritative situated evidence while excluding participant projection. | Code | Work | #69; strengthened for #71 attachment |
| `cast/practitioner/obligations.py` | Typed Runtime Obligations, discharge mechanisms, obligation plan, and four-status evaluation. | Code | Current | Added by #47 (issue #32). Obligations do not compile to capability demands; the firewall is structural |
| `cast/practitioner/concurrency.py` | Observed pre-state identity, conflict detection, optimistic commit validation, and reservations with deterministic acquisition order. | Code | Current | Added by #49 (issue #30). Retry is a new attempt, never a resumed closure |
| `cast/practitioner/crossing.py` | CrossingPlan, Brink observation, Closure, canonical `plan_digest`, and post-Closure verification. Closure deep-snapshots the complete plan graph before digesting so later mutation of the caller's open plan cannot rewrite `ClosedPlan` material. | Code | Work | #34 contract complete; immutability defect exposed and corrected by #73 |
| `cast/practitioner/situation_crossing.py` | Pre-Closure attachment from exact #69 Situation evidence into the existing CrossingPlan contract; reconstructs Environment receipts, re-compiles obligations, and refuses any Demand/receipt/attenuated-handle mismatch. Never observes Brink or calls Closure. | Code | Work | #71 complete by PR #72 |
| `cast/practitioner/brink_closure.py` | Observed-Brink Closure seam: retains a non-authorizing construction receipt, verifies exact #71 attachment before and after independent probes, rejects caster/Technique self-observation, and calls the existing #34 Closure without Mana movement or execution. | Code | Work | #73 |
| `cast/practitioner/__init__.py` | Practitioner public exports. | Code | Current | — |

The three transitional composition symlinks under cast — pointing at the Familiar domain, the Spell format, and Owl — were aids after the domain move, never duplicate authorities. They were removed under #17: runtime code resolves another domain's artifacts through `cast/kernel/resources.py` by canonical repository path, so the supported test command no longer depends on whether the checkout can materialize symlinks. Their paths are named without backticks here deliberately, so the completeness check does not read a historical note as a live inventory claim.

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
| `cast/tests/fixtures/domain-handle-environment-69.json` | Synthetic attributable Environment observations plus one concrete capability receipt for the #69 Situation seam. |
| `cast/tests/test_kernel.py` | Compatibility Kernel mechanics: closure, authority refusal, cost, duration, scope bound. |
| `cast/tests/test_candidate_requirements.py` | Requirement-centered candidate behavior through the adapter. |
| `cast/tests/test_casting_04.py` | 0.4 binding and enforcement mechanics. Formerly carried the Scope containment defect as an `expectedFailure`; #44 closed it and the specimen now passes. |
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
| `cast/tests/test_format_generations_55.py` | The two incompatible FORMAT 0.3 generations, pinned as running code. Documents a defect; every assertion is expected to change when #55 closes. |
| `cast/tests/test_crossing_plan_34.py` | CrossingPlan contract, clean/unobservable/nonzero Brink refusal, canonical plan identity, Closure snapshot integrity, and adversarial post-Closure swaps of target, Technique, binding, authority, obligation, evidence contract, residual bounds and Mana. |
| `cast/tests/test_domain_handle_67.py` | Read-only Domain Handle resolution: source identity, disagreement/unknown preservation, participant-relative projection, copy isolation, and no Cast/Environment dependency. |
| `cast/tests/test_handle_situation_69.py` | Domain Handle re-resolution against Environment evidence: source-digest verification, drift/unknown preservation, exact capability matching, participant invariance, and no Closure/execution path. |
| `cast/tests/test_situation_crossing_71.py` | Exact pre-Closure attachment from #69 Situation evidence into an open #34 CrossingPlan; rejects stale/recomputed binding tamper, Demand substitution, unresolved evidence, capability gaps, and all Closure/execution paths. |
| `cast/tests/test_brink_closure_73.py` | Independent pre-Closure Brink observation and exact Closure attachment; rejects missing/raising/self-certified probes, nonzero Cast-attributable deltas, plan/Situation mutation before or during observation, and proves Closure moves no Mana or Technique state. |
| `cast/tests/test_resource_resolution_17.py` | Canonical cross-domain resolution without composition symlinks, including a symlink-free checkout. |
| `cast/tests/test_familiar_revisions_15.py` | Immutable Familiar revisions addressable by `FamiliarRef`; a newer write does not destroy an older revision. |
| `cast/tests/test_familiar_view_14.py` | Every source guidance category accounted for exactly once; a silently dropped category fails. |
| `cast/tests/test_maintenance_replay_12.py` | Maintenance replay guarded on source identity and accepted receipt. |
| `cast/tests/test_capability_binding_13.py` | Typed demand binding to exact capability receipts; ambiguous and unsatisfiable demands fail closed. |
| `cast/tests/test_runtime_obligations_32.py` | Requirements compiling to typed obligations and four-status evaluation; a raising checker is `unresolved`, never satisfied. |
| `cast/tests/test_concurrent_casts_30.py` | Observed pre-state identity, conflict refusal naming both versions, and deterministic acquisition order. |
| `cast/tests/test_attestation_31.py` | Attestation envelope, signer provenance, and consumer-local trust policy above content digests. |
| `cast/tests/test_semantic_alignment_29.py` | Effect invariants and trials with evaluator provenance; a candidate cannot supply the trial that promotes itself. |
| `cast/tests/test_authority_enforcement_11.py` | Authority bound at the effect path through an attenuated credential, not only resolved at preflight. |
| `cast/tests/test_external_effects_27.py` | Irreversible external effects, compensation as a separate record, and the refusal of an executor certifying its own rollback. |
| `cast/tests/test_blast_radius_28.py` | Direct, declared, observed and unknown reactive reach beyond the attenuated handle. |
| `cast/tests/test_mana_tensor_06.py` | Sparse Mana tensor candidate: conservation, `Cost` contraction, and equal cost with unequal composition. |

**The suite no longer reports an expected failure.** `test_binding_scope_claim_alone_cannot_prove_environment_containment` was a `@unittest.expectedFailure` documenting the Scope containment defect as running code. #44 closed the defect and the specimen now passes as `test_environment_containment_stops_an_out_of_scope_mutation`. The marker is gone because the defect is closed, not because the test was deleted.

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

**Closed since the previous audit.** Each was a residual against an invariant above and is now met by merged, tested code or a completed Work contract. Listed as history, not as open work:

| Issue | Closed by | Met |
|---|---|---|
| #10 | #44 | Scope enforced at the effect path rather than preflight |
| #11 | #45 | Authority enforced through an attenuated execution capability |
| #12 | #41 | Maintenance replay guarded by source identity and accepted receipt |
| #13 | #43 | Requirements bound to exact capability receipts by typed demand |
| #14 | #42 | Familiar View omission accounting |
| #15 | #40 | Immutable Familiar revisions addressable by `FamiliarRef` |
| #17 | #39 | Runtime independence from transitional Git symlinks |
| #27 | #48 | Irreversible external effects and compensating Casts |
| #28 | #52 | Ambient reactive blast radius beyond direct capabilities |
| #29 | #51 | Semantic alignment evidence for autonomous Spellcraft |
| #30 | #49 | Concurrent Cast isolation and conflict semantics |
| #31 | #50 | Portable attestation and signer provenance above digests |
| #32 | #47 | Requirements compiled into typed runtime obligations |
| #34 | #63 | CrossingPlan / Brink / Closure contract defined and adversarially proven as Work; #73 subsequently corrected nested-plan snapshot immutability discovered by the first real practitioner Closure caller |
| #53 | #54 | Recorded lifecycle standing for the 0.3, 0.4, 0.5 and 0.6 generations |
| #71 | #72 | Exact Environment-evidenced Situation attached to a ready open CrossingPlan without crossing Closure |

**Ticket-owned residuals** — places where the implementation does not yet meet an invariant above, or where a required decision has not been recorded. Each is a live GitHub issue and none is restated here:

| Issue | Owns |
|---|---|
| #16 | Conserved Mana integrated with the invariant Cast lifecycle |
| #18 | This audit |
| #26 | Mana as typed sparse relations versus tensor product — open design work, not a gate on #16 |
| #56 | Adopt FORMAT 0.3 — including resolving **which of two incompatible 0.3 generations** it is, absorbed from #55. The Cast domain owns an admission schema the Spell domain does not generate |
| #57 · #58 · #59 | The remaining ladder rungs — KERNEL 0.4, 0.6 Magic participation, and the 0.5 disposition. See `LIFECYCLE_LADDER.md` |
| #73 | Independently observe the exact pre-Closure Brink and seal the #71 plan without moving Mana or executing |
| #35 · #36 · #37 · #38 | Milestone 0.7 proof-carrying crossing: post-execution observation seam, CAST sealing, adversarial conformance suite, and integration |

**Deferred by explicit decision, not by oversight:** remote Library transport and subscription, semantic-version range resolution, Presence lifetimes beyond a session, a Dismiss Spell, Level 0 semantics, portable Mana fields in `SPELL.md`, a universal sandbox implementation, a mandatory theorem prover, external PKI, and distributed consensus.

## What this commit actually proves

`README.md` and this audit must agree, and this section is what they agree on.

**Proven, by the CI run named at the top:** one local practitioner can cast Find Familiar, explicitly accept the resulting Familiar, persist it under a private host path, and resolve the exact artifact after restart. Registration, Presence, and the conserved Mana runtime each pass their own tests, and digest-chained ledger replay reconstructs conserved state across restart. The read-only Domain Handle and Situation seams preserve participant-relative projection separately from attributable Environment evidence and exact capability matching, and #71 attaches that situated evidence to a ready open CrossingPlan without crossing Closure.

Since the previous audit, the effect path itself became enforceable rather than merely resolved. Scope and Authority now bind through Environment-owned boundaries and refuse at closure when no boundary can be supplied (#10, #11). A violation the Technique caught and swallowed still fails the Cast, because the Kernel reads the boundary rather than the Technique's account of itself. Consequence is classified independently of executor status, and an executor cannot certify its own rollback (#27). Reactive reach beyond the attenuated handle is observed separately, so a Cast cannot claim a small radius because its handle was narrow (#28). Requirements bind to exact capability receipts by typed demand (#13) and compile to typed obligations that do not collapse into capability checks (#32). Concurrent Casts detect conflict on observed pre-state identity (#30). Familiar revisions are immutable and addressable (#15), View omission is accounted for exactly once (#14), and maintenance replay is guarded on source identity and accepted receipt (#12).

**Not proven, and not claimed:**

- that the Mana runtime participates in the Cast lifecycle at all — #16;
- that the Mana state shape is settled — #26, now open design work rather than a gate;
- that the full 0.7 crossing is integrated. CrossingPlan/Brink/Closure are completed contract Work (#34), exact Situation-to-open-plan attachment is completed Work (#71), and #73 is the bounded practitioner Closure caller under test; Mana commitment (#16), post-execution observation (#35), sealing (#36), conformance (#37), and reference-Kernel integration/adoption (#38) remain separate;
- that any of 0.3, 0.4, 0.5, or 0.6 is Current, Archive, or superseded by any other. Each is **retained as Work** under #53, which records their standing without taking a crossing. 0.2 remains the only Current specification, and the running Kernel exceeds it;
- that observation is exhaustive. Unknown reactive reach is representable and is recorded as unknown; it is not treated as absent.