# CAST 0.7 — immutable crossing account (Work)

**Status:** Work under issue #36. This does not promote KERNEL/FORMAT 0.7 or replace the Current 0.2 CAST schema.

A CAST record is the immutable attributable account of one Cast attempt. It is not the Cast itself and sealing does not imply successful Effect realization.

```text
record_digest != truth
record_digest != signature
signature != correctness
finding provenance != authority
executor success != Effect realization
```

`plan_digest` identifies the exact plan that crossed Closure. `record_digest` identifies the exact canonical CAST material. Either digest may later be the subject of a separate #31 attestation; neither is itself signer provenance or a trust decision.

## Minimal record

```text
CAST {
  cast_format,
  cast_id,
  plan_digest,
  recorded_configuration,
  capability_match_evidence,
  enforced_handle_receipts,
  mana_transitions,
  obligation_findings,
  observations,
  execution_trace,
  outcome,
  residuals,
  mana_settlement,
  status,
  record_digest
}
```

`status` is one of:

```text
successful | refused | aborted | violated | unresolved
```

A pre-Closure `refused` record has `plan_digest = null` because no ClosedPlan existed. Every other status is post-Closure and must name the exact `plan_digest`.

`aborted` means the executor attempt did not complete successfully after Closure; it does **not** mean no consequence occurred. Consequence and residual evidence remain separately recorded.

`violated` means at least one evaluated obligation is `violated`. `unresolved` means required crossing standing remains unknown/unresolved. A seal can therefore be valid while the crossing it records was not successful.

## Canonicalization

`record_digest` is SHA-256 over UTF-8 canonical JSON of every field above except `record_digest` itself:

- mapping keys sorted recursively;
- no insignificant whitespace;
- list order preserved because event/trace order is evidence;
- caller-owned values copied into plain JSON material;
- `record_digest` excluded from its own preimage.

The reference implementation stores canonical JSON text as the sealed state and reparses it for readers. Mutating caller input or a returned dictionary therefore cannot rewrite the record.

## Evidence ownership

The seal composes existing evidence rather than re-deciding it:

- ClosedPlan / `plan_digest` — #34/#73;
- capability matches and attenuated handles — #13/#71;
- conserved Mana events/settlement — #16;
- obligation findings and raw observations — #32/#35;
- consequence/residual account — #27/#35;
- signer attestation, if desired — separate #31 Registry layer.

Replay protections also remain where they already live: Cast/Mana replay is #16; maintenance source/receipt replay is #12. A digest does not replace either mechanism.
