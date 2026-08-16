"""Attestation and signer provenance above content digests (issue #31).

SHA-256 content addressing gives integrity and exact identity. It does not
establish who authored, approved, observed, or published an artifact, so
imported Spellbooks, CAST records, Familiar revisions and maintenance evidence
cannot derive external trust from a digest alone.
"""

from __future__ import annotations

import json
import unittest

from registry.attestation import (
    ACCEPTED,
    ATTESTATION_FORMAT,
    DIGEST_MISMATCH,
    HMAC_SHA256,
    INVALID,
    REJECTED,
    ROLES,
    UNVERIFIABLE,
    VERIFIED,
    Attestation,
    AttestationError,
    KeyResolver,
    LocalKey,
    TrustPolicy,
    attest,
    digest_of,
    verify,
)

PAYLOAD = b'{"spell":"bounded-work","version":"0.0.0"}'
TAMPERED = b'{"spell":"bounded-work","version":"9.9.9"}'


def keyring():
    author = LocalKey("local:author", b"author-secret")
    auditor = LocalKey("local:auditor", b"auditor-secret")
    return author, auditor, KeyResolver([author, auditor])


class DistinctionTests(unittest.TestCase):
    """digest != signature != attestation != trust decision."""

    def test_a_digest_is_not_a_signature(self):
        """Anyone can compute one, so it says nothing about origin."""
        self.assertEqual(digest_of(PAYLOAD), digest_of(PAYLOAD))
        # No key, no signer, no role anywhere in it.
        self.assertTrue(digest_of(PAYLOAD).startswith("sha256:"))
        self.assertEqual(71, len(digest_of(PAYLOAD)))

    def test_a_signature_is_not_an_attestation(self):
        """The envelope carries who and in what capacity; raw bytes do not."""
        author, _auditor, _resolver = keyring()
        attestation = attest(digest_of(PAYLOAD), author, signer="bdo", role="author")
        self.assertTrue(attestation.signature)
        self.assertEqual("bdo", attestation.signer)
        self.assertEqual("author", attestation.role)
        self.assertEqual("local:author", attestation.verification)

    def test_an_attestation_is_not_a_trust_decision(self):
        """Same verified evidence, two policies, two correct answers."""
        author, _auditor, resolver = keyring()
        attestation = attest(digest_of(PAYLOAD), author, signer="bdo", role="author")
        checked = [verify(attestation, PAYLOAD, resolver)]
        self.assertTrue(checked[0].ok)

        permissive = TrustPolicy()
        demanding = TrustPolicy(require_roles=("auditor",))

        self.assertTrue(permissive.decide(checked).accepted)
        self.assertFalse(demanding.decide(checked).accepted)

    def test_verification_does_not_decide_trust(self):
        author, _auditor, resolver = keyring()
        attestation = attest(digest_of(PAYLOAD), author, signer="a-stranger", role="publisher")
        result = verify(attestation, PAYLOAD, resolver)

        # It verifies: the holder of that key really did vouch for these bytes.
        self.assertEqual(VERIFIED, result.status)
        # It is still rejected by a consumer that does not believe the signer.
        decision = TrustPolicy(trusted_signers=("bdo",), allow_unattested=False).decide([result])
        self.assertEqual(REJECTED, decision.status)


class EnvelopeTests(unittest.TestCase):
    def test_the_envelope_round_trips_portably(self):
        author, _auditor, _resolver = keyring()
        attestation = attest(
            digest_of(PAYLOAD), author, signer="bdo", role="author",
            issued="2026-08-16T00:00:00Z", chain=("local:root",), detail={"note": "first seal"},
        )
        restored = Attestation.from_dict(json.loads(json.dumps(attestation.as_dict())))
        self.assertEqual(attestation, restored)

    def test_the_envelope_carries_no_artifact_bytes(self):
        author, _auditor, _resolver = keyring()
        described = attest(digest_of(PAYLOAD), author, signer="bdo", role="author").as_dict()
        self.assertNotIn(PAYLOAD.decode(), json.dumps(described))
        self.assertEqual(digest_of(PAYLOAD), described["artifact_digest"])

    def test_a_malformed_envelope_is_refused(self):
        author, _auditor, _resolver = keyring()
        good = attest(digest_of(PAYLOAD), author, signer="bdo", role="author")
        for field, value, message in (
            ("role", "overlord", "unknown attestation role"),
            ("scheme", "wishful", "unknown attestation scheme"),
            ("artifact_digest", "md5:abc", "not a content digest"),
            ("signer", "", "requires signer"),
            ("attestation_format", "9.9", "unsupported attestation format"),
        ):
            with self.subTest(field=field):
                broken = good.as_dict()
                broken[field] = value
                with self.assertRaisesRegex(AttestationError, message):
                    Attestation.from_dict(broken)

    def test_an_unknown_role_cannot_be_attested(self):
        author, _auditor, _resolver = keyring()
        with self.assertRaisesRegex(AttestationError, "unknown attestation role"):
            attest(digest_of(PAYLOAD), author, signer="bdo", role="overlord")

    def test_the_declared_roles_are_the_ones_the_issue_names(self):
        self.assertEqual(("author", "auditor", "observer", "publisher", "accepter"), ROLES)


class LocalSigningPathTests(unittest.TestCase):
    def test_a_local_offline_attestation_verifies(self):
        author, _auditor, resolver = keyring()
        attestation = attest(digest_of(PAYLOAD), author, signer="bdo", role="author")
        self.assertEqual(HMAC_SHA256, attestation.scheme)
        self.assertTrue(verify(attestation, PAYLOAD, resolver).ok)

    def test_tampered_content_fails_verification(self):
        author, _auditor, resolver = keyring()
        attestation = attest(digest_of(PAYLOAD), author, signer="bdo", role="author")

        result = verify(attestation, TAMPERED, resolver)

        self.assertEqual(DIGEST_MISMATCH, result.status)
        self.assertEqual(digest_of(TAMPERED), result.detail["actual"])

    def test_tampering_does_not_change_the_content_addressing_rule(self):
        """The digest of the tampered bytes is still a correct digest of them."""
        self.assertEqual(digest_of(TAMPERED), digest_of(TAMPERED))
        self.assertNotEqual(digest_of(PAYLOAD), digest_of(TAMPERED))
        # Verification failed above; the addressing rule itself is untouched.

    def test_a_forged_signature_is_invalid(self):
        author, _auditor, resolver = keyring()
        attestation = attest(digest_of(PAYLOAD), author, signer="bdo", role="author")
        forged = Attestation.from_dict({**attestation.as_dict(), "signature": "0" * 64})

        self.assertEqual(INVALID, verify(forged, PAYLOAD, resolver).status)

    def test_relabelling_the_role_invalidates_the_signature(self):
        """Signer and role are inside the signed material, not beside it."""
        author, _auditor, resolver = keyring()
        attestation = attest(digest_of(PAYLOAD), author, signer="bdo", role="observer")
        relabelled = Attestation.from_dict({**attestation.as_dict(), "role": "auditor"})

        self.assertEqual(INVALID, verify(relabelled, PAYLOAD, resolver).status)

    def test_reattributing_the_signer_invalidates_the_signature(self):
        author, _auditor, resolver = keyring()
        attestation = attest(digest_of(PAYLOAD), author, signer="bdo", role="author")
        reattributed = Attestation.from_dict({**attestation.as_dict(), "signer": "someone-else"})

        self.assertEqual(INVALID, verify(reattributed, PAYLOAD, resolver).status)

    def test_an_unresolvable_key_is_unverifiable_not_invalid(self):
        """A consumer that cannot check is not thereby entitled to reject the content."""
        author, _auditor, _resolver = keyring()
        attestation = attest(digest_of(PAYLOAD), author, signer="bdo", role="author")

        result = verify(attestation, PAYLOAD, KeyResolver([]))

        self.assertEqual(UNVERIFIABLE, result.status)
        self.assertNotEqual(INVALID, result.status)


class MultipleAttestationTests(unittest.TestCase):
    def test_attestations_by_different_roles_coexist_for_one_artifact(self):
        author, auditor, resolver = keyring()
        digest = digest_of(PAYLOAD)
        attestations = [
            attest(digest, author, signer="bdo", role="author"),
            attest(digest, auditor, signer="owl", role="auditor"),
            attest(digest, auditor, signer="owl", role="observer"),
        ]
        results = [verify(item, PAYLOAD, resolver) for item in attestations]

        self.assertTrue(all(item.ok for item in results))
        self.assertEqual({"author", "auditor", "observer"}, {item.attestation.role for item in results})
        self.assertEqual({digest}, {item.attestation.artifact_digest for item in results})

    def test_a_policy_requiring_two_roles_is_satisfied_only_when_both_verify(self):
        author, auditor, resolver = keyring()
        digest = digest_of(PAYLOAD)
        policy = TrustPolicy(require_roles=("author", "auditor"), allow_unattested=False)

        only_author = [verify(attest(digest, author, signer="bdo", role="author"), PAYLOAD, resolver)]
        self.assertEqual(REJECTED, policy.decide(only_author).status)
        self.assertIn("auditor", policy.decide(only_author).reason)

        both = only_author + [
            verify(attest(digest, auditor, signer="owl", role="auditor"), PAYLOAD, resolver)
        ]
        self.assertEqual(ACCEPTED, policy.decide(both).status)
        self.assertEqual(2, len(policy.decide(both).verified))


class LocalPolicyTests(unittest.TestCase):
    def test_applying_a_policy_rewrites_neither_artifact_nor_attestation(self):
        author, _auditor, resolver = keyring()
        attestation = attest(digest_of(PAYLOAD), author, signer="bdo", role="author")
        before_payload = bytes(PAYLOAD)
        before_envelope = attestation.as_dict()

        TrustPolicy(require_roles=("auditor",)).decide([verify(attestation, PAYLOAD, resolver)])

        self.assertEqual(before_payload, PAYLOAD)
        self.assertEqual(before_envelope, attestation.as_dict())

    def test_two_consumers_reach_different_decisions_about_the_same_evidence(self):
        author, _auditor, resolver = keyring()
        checked = [verify(attest(digest_of(PAYLOAD), author, signer="bdo", role="author"), PAYLOAD, resolver)]

        self.assertTrue(TrustPolicy(trusted_signers=("bdo",)).decide(checked).accepted)
        self.assertFalse(
            TrustPolicy(trusted_signers=("someone-else",), require_roles=("author",))
            .decide(checked).accepted
        )

    def test_unattested_content_remains_usable_where_policy_permits(self):
        permissive = TrustPolicy(allow_unattested=True)
        strict = TrustPolicy(allow_unattested=False)

        self.assertTrue(permissive.decide([]).accepted)
        self.assertIn("permitted by policy", permissive.decide([]).reason)
        self.assertFalse(strict.decide([]).accepted)

    def test_absence_of_an_attestation_is_not_invalid_content(self):
        """Unauthenticated provenance and invalid content are different facts."""
        decision = TrustPolicy(allow_unattested=False).decide([])
        self.assertEqual(REJECTED, decision.status)
        self.assertIn("requires attestation", decision.reason)
        self.assertNotIn("invalid", decision.reason)


class ExistingDigestFieldTests(unittest.TestCase):
    """SHA-256 fields keep their names and their meaning."""

    def test_the_registry_scroll_digest_is_still_an_integrity_digest(self):
        from pathlib import Path

        from registry import Scroll, seal_scroll

        spell_text = (
            Path(__file__).resolve().parents[1] / "examples" / "summon-familiar" / "SPELL.md"
        ).read_text(encoding="utf-8")
        sealed = seal_scroll(spell_text, scroll_id="summon-familiar-0.1.0")
        scroll = Scroll.from_dict(sealed)

        self.assertTrue(scroll.digest.startswith("sha256:"))
        # Not renamed, not relabelled as a signature, and no attestation field
        # was added to the sealed carrier by this work.
        self.assertNotIn("signature", sealed)
        self.assertNotIn("attestation", sealed)

    def test_this_module_uses_the_same_content_addressing_rule(self):
        from hashlib import sha256

        self.assertEqual("sha256:" + sha256(PAYLOAD).hexdigest(), digest_of(PAYLOAD))

    def test_the_attestation_format_is_declared(self):
        self.assertEqual("0.1", ATTESTATION_FORMAT)


if __name__ == "__main__":
    unittest.main()
