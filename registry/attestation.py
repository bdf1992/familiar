"""Attestation and signer provenance above content digests.

Content addressing gives integrity and exact identity. It does not say who
authored, approved, observed, or published anything. An imported Spellbook, a
CAST record, a Familiar revision, and maintenance evidence all carry SHA-256
digests today and none of them carries provenance, so external trust cannot be
derived from what exists.

Four things are distinct, and collapsing any adjacent pair is the defect this
layer exists to prevent:

```text
digest           this is exactly these bytes
signature        someone holding a key vouched for that digest
attestation      a signature plus who, in what role, verifiable how
trust decision   whether THIS consumer accepts that attestation, now
```

A digest is not a signature: it proves nothing about origin, and anyone can
compute one. A signature is not an attestation: bare bytes vouch for a digest
without saying in what capacity. An attestation is not a trust decision: it is
evidence a consumer weighs under its own policy, and two consumers may weigh
the same attestation differently and both be right.

**Attestations live beside the artifact, never inside it.** Adding one must not
change the artifact's digest, or attesting would alter the identity being
attested to. Content-addressing rules are untouched by this module, and the
existing SHA-256 fields keep their names and their meaning: they remain
integrity digests and are not signatures.

**Absence of an attestation means unauthenticated provenance, not invalid
content.** Local-first artifacts stay usable wherever policy permits.

The reference signing path is local and offline. It uses HMAC-SHA256, which is
a **symmetric** message authentication code: anyone who can verify can also
sign. That is honest for a single-owner local-first store and is deliberately
not called a signature scheme with non-repudiation. The envelope names its
scheme so a public-key or Sigstore-style identity can be added as another
scheme without the envelope, the policy layer, or any stored artifact changing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import hmac
from typing import Any, Iterable, Mapping, Sequence

#: Roles an attestation may claim. A role is a claim about capacity, not a grant.
ROLES = ("author", "auditor", "observer", "publisher", "accepter")

HMAC_SHA256 = "hmac-sha256"
SCHEMES = (HMAC_SHA256,)

ATTESTATION_FORMAT = "0.1"


class AttestationError(ValueError):
    """An attestation or key could not be expressed."""


def digest_of(payload: bytes) -> str:
    """The same content-addressing rule the rest of the repository uses."""
    return "sha256:" + sha256(payload).hexdigest()


@dataclass(frozen=True)
class LocalKey:
    """A local/offline symmetric key. Verifying and signing are the same power."""

    reference: str
    secret: bytes

    def __post_init__(self) -> None:
        if not isinstance(self.reference, str) or not self.reference:
            raise AttestationError("a local key requires a reference")
        if not isinstance(self.secret, (bytes, bytearray)) or not self.secret:
            raise AttestationError("a local key requires secret material")


class KeyResolver:
    """Maps a verification reference to key material a consumer holds.

    A consumer that cannot resolve a reference cannot verify. That is an
    unverifiable attestation, not an invalid artifact.
    """

    def __init__(self, keys: Iterable[LocalKey] = ()):
        self._keys = {key.reference: key for key in keys}

    def add(self, key: LocalKey) -> None:
        self._keys[key.reference] = key

    def resolve(self, reference: str) -> LocalKey | None:
        return self._keys.get(reference)


@dataclass(frozen=True)
class Attestation:
    """A portable envelope binding a signer and role to an exact digest.

    It carries no artifact bytes. It names a digest, so it can travel with the
    artifact, separately from it, or in a sidecar index, without ever being
    part of what it attests to.
    """

    attestation_format: str
    artifact_digest: str
    signer: str
    role: str
    scheme: str
    verification: str
    signature: str
    issued: str | None = None
    chain: tuple[str, ...] = ()
    detail: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.attestation_format != ATTESTATION_FORMAT:
            raise AttestationError(f"unsupported attestation format: {self.attestation_format}")
        if self.role not in ROLES:
            raise AttestationError(f"unknown attestation role: {self.role}")
        if self.scheme not in SCHEMES:
            raise AttestationError(f"unknown attestation scheme: {self.scheme}")
        if not self.artifact_digest.startswith("sha256:") or len(self.artifact_digest) != 71:
            raise AttestationError(f"not a content digest: {self.artifact_digest}")
        for name in ("signer", "verification", "signature"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                raise AttestationError(f"an attestation requires {name}")

    def as_dict(self) -> dict[str, Any]:
        described = {
            "attestation_format": self.attestation_format,
            "artifact_digest": self.artifact_digest,
            "signer": self.signer,
            "role": self.role,
            "scheme": self.scheme,
            "verification": self.verification,
            "signature": self.signature,
            "chain": list(self.chain),
            "detail": dict(self.detail),
        }
        if self.issued is not None:
            described["issued"] = self.issued
        return described

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "Attestation":
        return cls(
            attestation_format=value["attestation_format"],
            artifact_digest=value["artifact_digest"],
            signer=value["signer"],
            role=value["role"],
            scheme=value["scheme"],
            verification=value["verification"],
            signature=value["signature"],
            issued=value.get("issued"),
            chain=tuple(value.get("chain", ())),
            detail=dict(value.get("detail", {})),
        )


def _signing_material(artifact_digest: str, signer: str, role: str, issued: str | None) -> bytes:
    """Bind signer and role into the signed bytes.

    Signing the digest alone would let an attestation be relabelled into
    another role, or reattributed, without invalidating it.
    """
    return "\n".join([ATTESTATION_FORMAT, artifact_digest, signer, role, issued or ""]).encode("utf-8")


def attest(
    artifact_digest: str,
    key: LocalKey,
    *,
    signer: str,
    role: str,
    issued: str | None = None,
    chain: Sequence[str] = (),
    detail: Mapping[str, Any] | None = None,
) -> Attestation:
    """Produce an attestation over an exact digest. The artifact is not touched."""
    if role not in ROLES:
        raise AttestationError(f"unknown attestation role: {role}")
    material = _signing_material(artifact_digest, signer, role, issued)
    signature = hmac.new(key.secret, material, sha256).hexdigest()
    return Attestation(
        attestation_format=ATTESTATION_FORMAT,
        artifact_digest=artifact_digest,
        signer=signer,
        role=role,
        scheme=HMAC_SHA256,
        verification=key.reference,
        signature=signature,
        issued=issued,
        chain=tuple(chain),
        detail=dict(detail or {}),
    )


VERIFIED = "verified"
UNVERIFIABLE = "unverifiable"
INVALID = "invalid"
DIGEST_MISMATCH = "digest_mismatch"


@dataclass(frozen=True)
class Verification:
    """The result of checking one attestation. Not a decision to trust it."""

    status: str
    attestation: Attestation
    detail: Mapping[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.status == VERIFIED


def verify(
    attestation: Attestation,
    payload: bytes,
    resolver: KeyResolver,
) -> Verification:
    """Check that this signer vouched for these exact bytes in this role.

    Says nothing about whether the signer should be believed. That is the
    policy layer's question and deliberately not answered here.
    """
    actual = digest_of(payload)
    if actual != attestation.artifact_digest:
        return Verification(
            DIGEST_MISMATCH, attestation,
            {"expected": attestation.artifact_digest, "actual": actual},
        )
    key = resolver.resolve(attestation.verification)
    if key is None:
        return Verification(
            UNVERIFIABLE, attestation,
            {"reason": f"no key material for {attestation.verification!r}"},
        )
    material = _signing_material(
        attestation.artifact_digest, attestation.signer, attestation.role, attestation.issued
    )
    expected = hmac.new(key.secret, material, sha256).hexdigest()
    if not hmac.compare_digest(expected, attestation.signature):
        return Verification(INVALID, attestation, {"reason": "signature does not match"})
    return Verification(VERIFIED, attestation, {"signer": attestation.signer, "role": attestation.role})


ACCEPTED = "accepted"
REJECTED = "rejected"


@dataclass(frozen=True)
class TrustDecision:
    status: str
    reason: str
    verified: tuple[Attestation, ...] = ()

    @property
    def accepted(self) -> bool:
        return self.status == ACCEPTED


@dataclass(frozen=True)
class TrustPolicy:
    """A consumer's local rule for what counts as sufficient provenance.

    Applying a policy never edits the artifact or the attestations. Two
    consumers may reach different decisions about the same evidence and both be
    correct, which is why this is separate from verification.
    """

    #: Roles that must each be present and verified.
    require_roles: tuple[str, ...] = ()
    #: Signers this consumer is willing to believe. Empty means any.
    trusted_signers: tuple[str, ...] = ()
    #: Whether an artifact with no attestation at all may still be used.
    allow_unattested: bool = True

    def decide(self, verifications: Sequence[Verification]) -> TrustDecision:
        verified = tuple(item.attestation for item in verifications if item.ok)

        if not verifications:
            if self.allow_unattested:
                return TrustDecision(ACCEPTED, "unattested content permitted by policy")
            return TrustDecision(REJECTED, "policy requires attestation and none is present")

        if self.trusted_signers:
            verified = tuple(item for item in verified if item.signer in self.trusted_signers)

        present = {item.role for item in verified}
        missing = [role for role in self.require_roles if role not in present]
        if missing:
            return TrustDecision(
                REJECTED, f"missing verified attestation for role(s): {', '.join(missing)}", verified
            )
        if not verified and not self.allow_unattested:
            return TrustDecision(REJECTED, "no attestation verified under this policy", verified)
        return TrustDecision(ACCEPTED, "policy satisfied", verified)
