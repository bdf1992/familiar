# Registry Domain

Registry owns identity, addressability, carriers, registration, exact resolution, provenance, Spellbooks, Libraries, and Registrar relations.

Knowledge/addressability may change here without attempting an Effect. Registration is not casting.

Current material already here:

- `core.py`
- `local.py` — optional restart-safe local persistence for existing Spellbook objects
- Scroll, Spellbook, and Library schemas

`LocalRegistry` is a storage adapter, not a publication mechanism. A personal book may remain entirely local. The adapter preserves exact declaration verification on reopen and uses atomic writes plus private POSIX permissions where the host supports them. Host disk encryption and account access control remain environment responsibilities; local persistence does not claim issuer authentication or a signature trust chain.

## Attestation

Four things are distinct and adjacent pairs are easy to collapse:

```text
digest           this is exactly these bytes
signature        someone holding a key vouched for that digest
attestation      a signature plus who, in what role, verifiable how
trust decision   whether THIS consumer accepts that attestation, now
```

`registry/attestation.py` adds the third and fourth as an **optional** layer. Content identity remains valid without one: absence of an attestation means unauthenticated provenance, not invalid content, and local-first artifacts stay usable wherever policy permits.

**Attestations live beside the artifact, never inside it.** Adding one does not change the artifact's digest, because attesting must not alter the identity being attested to. The existing SHA-256 fields keep their names and their meaning — they are integrity digests and are not signatures.

Signer and role are inside the signed material, so an attestation cannot be relabelled into another role or reattributed to another signer without invalidating it.

The reference signing path is local and offline and uses HMAC-SHA256, which is a **symmetric** MAC: anyone who can verify can also sign. That is honest for a single-owner local-first store and is deliberately not presented as a signature scheme with non-repudiation. The envelope names its scheme, so a public-key or Sigstore-style identity can be added as another scheme without changing the envelope, the policy layer, or any stored artifact.

Verification and trust are separate calls. Verification answers whether this signer vouched for these exact bytes in this role. Trust is a consumer-local policy decision over verified attestations, and two consumers may decide differently about the same evidence and both be right.

Registrar `.Binding` belongs to this domain when it answers where and how an artifact participates in registration. Technique Binding does not; Technique Binding belongs to Cast because it describes an execution path.
