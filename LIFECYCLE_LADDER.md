# The lifecycle ladder

Status: Work + Knowledge. This document specifies a **route**, not a standing. It adopts nothing, archives nothing, and promotes nothing. Each rung is a crossing that must still be taken and recorded on its own terms.

`FOUNDATIONS.md` states that *"Work becomes Current only through explicit adoption"* and that *"an invalid or implicit crossing should be noticeable rather than normalized away."* It says what a crossing **is**. It does not say how a repository gets from one Current generation to a much later one when several generations of Work have accumulated in between.

This document is that missing piece: the ordered sequence of crossings from **FORMAT/KERNEL 0.2 Current** to **0.7 Current**.

## Why a ladder is needed at all

Under #53 every draft generation was recorded as **retained** as Work, and the reason was not indecision. Each generation says in its own header that it extends, derives from, or sits beneath what came before:

```text
0.3 kernel   "does not replace the current reference Kernel yet"
0.4          "extends the requirement-centered 0.3 work"
0.6          "adds Magic participation beneath the existing invariant casting law"
```

**Nothing ever replaced anything.** That is why no supersession could be recorded, and it is also why the version numbers do not form a ladder on their own. They are layers stacked beside a Current 0.2 that none of them ever displaced.

A layer stack is not a route. **0.7 cannot be reached by promoting it, because promoting it would step over four generations that were never crossed** — precisely the silent promotion #38's own acceptance criteria forbid. The gap has to be walked, not jumped.

## Where the repository actually stands

The important fact is not in the documents. **The runtime is already a stack of wrappers, one per generation, and it stamps which generation it is operating at.**

```text
cast/validation/casting_04.py       validates Technique Binding      cast_format "0.4-draft"
        wraps ↓
cast/validation/candidate_adapter.py  normalizes 0.3 declarations    cast_format "0.3-candidate"
        wraps ↓
cast/kernel/spell_kernel.py           the Kernel that actually runs  cast_format "0.2"
```

`cast/kernel/spell_kernel.py` validates against `spell/format/spell.schema.json` — the **0.2** format — and emits a 0.2 CAST. Everything above it is reconstruction by a wrapper.

Three consequences follow, and each one shapes a rung:

**The Kernel exceeds its own specification.** Scope and Authority effect-path enforcement, typed capability binding, runtime obligations, concurrency isolation, consequence classification and blast-radius observation all live in `cast/kernel/spell_kernel.py`. None is described by KERNEL 0.2. The code ran ahead of the record.

**The 0.4 casting law is enforced by a wrapper, not by the Kernel.** `cast/validation/casting_04.py` owns Technique Binding validation and emits the 0.4 CAST record. The Kernel underneath it neither knows nor enforces that contract.

**Two different 0.3 candidate schemas exist.** `spell/format/0.3-draft/spell.schema.json` is generated from `spell/format/0.3-draft/models.py` and is not loaded by anything at runtime. `cast/validation/candidate/spell.schema.json` is a separate, smaller, hand-maintained file, and it is the one the adapter actually validates against. They are not the same document. **The Spell domain owns declaration format, and the Cast domain is carrying a divergent shadow copy of it.**

## The rungs

Each rung states what must be true to step onto it, what crosses when it is taken, and what evidence records the crossing. A rung is not taken by editing this file.

---

### Rung 0 — Reconcile the divergent 0.3 schemas

**Owner: #55.**

**Not a crossing.** A prerequisite, and a defect in its own right.

One 0.3 declaration schema must exist, owned by the Spell domain, generated from `spell/format/0.3-draft/models.py`. `cast/validation/candidate_adapter.py` must validate against that canonical artifact through `cast/kernel/resources.py` rather than against a private copy.

**Entry:** none. Available now.
**Crosses:** nothing. The shadow copy is deleted, not archived — it was never an authority.
**Evidence:** the adapter's existing tests pass against the generated schema; a drift check fails if the two ever diverge again.

Until this is done, "adopt FORMAT 0.3" has no single referent.

---

### Rung 1 — Adopt FORMAT 0.3

**Owner: #56.**

**0.2 format → Archive. 0.3 format → Current.**

`spell/format/0.3-draft/SPECIFICATION.md` says *"FORMAT 0.2 remains Current until an explicit adoption crossing."* This is that crossing.

**Entry:** Rung 0 complete. The Kernel validates the 0.3 shape **directly** rather than receiving it through `cast/validation/candidate_adapter.py`.
**Crosses:** `spell/format/SPECIFICATION.md` and `spell/format/spell.schema.json` become Archive; the 0.3 material takes their place and loses the `-draft` designation.
**Evidence:** `cast_format` emitted by the Kernel is no longer `"0.2"`; the adapter's normalization layer is gone rather than bypassed; the full suite passes.

**The adapter disappears at this rung.** That is the point. An adapter exists to reach a format the Kernel does not speak; once the Kernel speaks it, keeping the adapter would preserve the wrapper stack this ladder exists to unwind.

---

### Rung 2 — Adopt KERNEL 0.4

**Owner: #57.**

**0.2 kernel → Archive. 0.4 → Current.**

**Entry:** Rung 1 complete. The invariant casting law and the Technique Binding boundary move from `cast/validation/casting_04.py` into `cast/kernel/spell_kernel.py`. CAST is emitted natively at 0.4 rather than reconstructed by a wrapper.

**Crosses:** `cast/kernel/KERNEL.md` and `cast/kernel/cast.schema.json` become Archive; `cast/kernel/0.4-draft/` material takes their place. `cast/kernel/0.3-draft/` becomes Archive here rather than at Rung 1, because 0.4 is what supersedes it — it extends the 0.3 kernel work, so the 0.3 kernel draft is only displaced once 0.4 stands in its place.

**Evidence:** `cast_format` is `"0.4"`; `cast/validation/casting_04.py` no longer wraps the Kernel; every currently passing test still passes.

**KERNEL 0.4's document must catch up to the code before it can be adopted.** The Kernel already enforces Scope and Authority at the effect path, binds typed capability demands, compiles runtime obligations, isolates concurrent Casts, classifies consequence, and observes reactive reach. KERNEL 0.4 describes none of that. **Adopting a specification that understates what the code does would recreate the exact gap this ladder is closing** — one rung higher and harder to see. This rung is therefore mostly writing, and the writing is the work.

---

### Step aside — Disposition the 0.5 documents

**Owner: #59.**

**Not a rung.** 0.5 is not a kernel generation and nothing in it can be adopted as a runtime specification. It is practitioner and registry integration narrative: `cast/work/docs/PRACTITIONER_LOOP_0_5.md` and `cast/work/docs/REGISTRY_AND_SUMMONING_0_5.md`.

It still needs a disposition, because #38 requires that documentation not silently promote older draft generations and an undispositioned 0.5 leaves that unsatisfiable. The live content folds into whatever documents are Current after Rung 2 and the originals are retired, or they are explicitly retained with a reason. `spell/migration/LEDGER.md` already proposes splitting `REGISTRY_AND_SUMMONING_0_5.md` by owner and notes it may be retired outright rather than archived.

This can be taken in parallel with any rung. It blocks only #38.

---

### Rung 3 — Adopt 0.6 Magic participation

**Owner: #58.**

**0.6 → Current.** Nothing is archived; 0.6 sits *beneath* the casting law rather than replacing it, so this rung **adds** a Current layer instead of displacing one.

**Entry:** #16. A Cast must actually reach the Magic runtime. Today `cast/kernel/spell_kernel.py` contains no Mana participation at all, and `environment/magic.py` passes its own tests without any Cast ever calling it. **A specification of participation cannot be adopted while nothing participates.**

**Crosses:** `cast/kernel/0.6-draft/KERNEL.md` and `environment/MAGIC.md` become Current.
**Evidence:** a Mana-bearing Cast crosses Closure exactly once, conservation holds through the integrated flow, and a refused Cast leaves conserved state unchanged.

#26 informs this rung and does not gate it. Whether Mana state is a typed sparse tuple or a tensor product changes the representation, not whether participation happens.

---

### Rung 4 — 0.7

**Owner: #38**, over #34, #35, #36, #37.

**0.7 → Current.** The crossing #38 owns.

**Entry:** Rungs 1 through 3 taken, 0.5 dispositioned, and #34, #35, #36, #37 complete.
**Crosses:** as #38's promotion crossing specifies, and not before its acceptance criteria and attributable CI evidence exist.

**0.7 must be authored as the Kernel's specification, not as `0.7-draft/` beside it.** Every previous generation became a layer because it was written as a draft next to the code instead of a description of it. Repeating that pattern would make this ladder six rungs long instead of five and would leave the same gap at the top. #34 already points the right way, offering *"an explicitly equivalent extension of the existing `CastPlan`"* as an acceptable shape.

---

## Why climbing is cheaper than jumping

The ladder is not only a compliance route. **Rungs 1 and 2 are the refactor that makes 0.7 buildable.**

0.7 defines a closed-plan contract, an observation seam, and a canonical sealed record — all of which have to attach to the Kernel. Built today they would attach to a three-layer wrapper stack in which the Kernel speaks 0.2, an adapter speaks 0.3, and a validation module speaks 0.4. The closed plan would have to be identified across all three, and `plan_digest` would have to mean something stable while three layers each reconstruct the record differently.

Unwrapping that stack first is not a detour taken for the sake of the lifecycle record. It is the ground #34 needs to stand on, and the lifecycle record is what it buys along the way.

## What this document does not do

- It does not take any crossing. Every rung remains untaken until its own change lands with its own evidence.
- It does not promote, adopt, archive, or retire anything, and it does not change any artifact's standing.
- It does not decide #26's representation question or #38's promotion.
- It does not rewrite any historical seal or dated record.
- It is not a schedule. The rungs are ordered by dependency, not by date.

The standing of each generation as it exists today is recorded in `REPOSITORY_AUDIT.md` § *Lifecycle generations*, and that record remains authoritative until a rung is actually taken.
