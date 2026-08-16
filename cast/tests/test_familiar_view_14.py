"""Familiar View omission accounting is mechanically complete (issue #14).

The View contract rests on `omission != absence`. While the schema allowed an
empty `guidance` object and made `omitted` optional, a schema-valid View could
reach a consumer without saying whether a source category had been represented
or withheld, and the consumer had no way to tell the two apart.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from familiar.store import FamiliarRef, FamiliarStore, FamiliarStoreError
from familiar.view import SOURCE_CATEGORIES, FamiliarViewError, build_view, validate_view


def familiar_candidate(attention: str = "collapsed distinctions") -> dict:
    return {
        "familiar_format": "0.3",
        "id": "bdo.familiar",
        "caster": {"id": "bdo", "kind": "human"},
        "dialect": {"description": "Compact distinction-first working language."},
        "attention": [attention],
        "preferences": ["small inspectable kernels"],
        "stake": ["practitioner agent work"],
        "advisory_authority": ["protocol quality"],
    }


def stored(root: Path, familiar: dict | None = None):
    store = FamiliarStore(root)
    ref = store.put(familiar or familiar_candidate(), caster_id="bdo")
    return store, ref


class OmissionAccountingTests(unittest.TestCase):
    def test_a_fully_represented_view_carries_an_explicit_empty_omission_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            store, ref = stored(Path(tmp) / "familiars")
            view = build_view(store, ref, policy="private", audience="bdo")

            self.assertEqual([], view["omitted"])
            self.assertEqual(set(SOURCE_CATEGORIES), set(view["guidance"]))
            validate_view(view)

    def test_a_partial_view_names_every_category_it_withheld(self):
        with tempfile.TemporaryDirectory() as tmp:
            store, ref = stored(Path(tmp) / "familiars")
            view = build_view(
                store,
                ref,
                policy="host",
                audience="some-host",
                represent=["dialect", "attention"],
            )

            self.assertEqual({"dialect", "attention"}, set(view["guidance"]))
            self.assertEqual(["preferences", "stake", "advisory_authority"], view["omitted"])
            validate_view(view)

    def test_a_fully_redacted_view_is_valid_only_when_every_category_is_omitted(self):
        with tempfile.TemporaryDirectory() as tmp:
            store, ref = stored(Path(tmp) / "familiars")
            view = build_view(store, ref, policy="public", audience="anyone", represent=[])

            self.assertEqual({}, view["guidance"])
            self.assertEqual(list(SOURCE_CATEGORIES), view["omitted"])
            validate_view(view)

    def test_a_view_with_an_unaccounted_category_is_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            store, ref = stored(Path(tmp) / "familiars")
            for category in SOURCE_CATEGORIES:
                with self.subTest(dropped=category):
                    view = build_view(store, ref, policy="private", audience="bdo")
                    del view["guidance"][category]
                    with self.assertRaisesRegex(FamiliarViewError, f"does not account for.*{category}"):
                        validate_view(view)

    def test_a_view_that_represents_and_omits_the_same_category_is_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            store, ref = stored(Path(tmp) / "familiars")
            for category in SOURCE_CATEGORIES:
                with self.subTest(doubled=category):
                    view = build_view(store, ref, policy="private", audience="bdo")
                    view["omitted"].append(category)
                    with self.assertRaisesRegex(FamiliarViewError, f"both represents and omits.*{category}"):
                        validate_view(view)

    def test_a_view_without_an_omission_set_is_invalid(self):
        """The old schema made `omitted` optional, which is what allowed the gap."""
        with tempfile.TemporaryDirectory() as tmp:
            store, ref = stored(Path(tmp) / "familiars")
            view = build_view(store, ref, policy="private", audience="bdo")
            del view["omitted"]
            with self.assertRaises(FamiliarViewError):
                validate_view(view)

    def test_an_empty_guidance_object_is_no_longer_silently_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            store, ref = stored(Path(tmp) / "familiars")
            view = build_view(store, ref, policy="private", audience="bdo")
            view["guidance"] = {}
            view["omitted"] = []
            with self.assertRaisesRegex(FamiliarViewError, "does not account for"):
                validate_view(view)

    def test_omitted_cannot_account_for_a_category_that_does_not_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            store, ref = stored(Path(tmp) / "familiars")
            view = build_view(store, ref, policy="host", audience="h", represent=["dialect"])
            view["omitted"] = ["attention", "preferences", "stake", "advisroy_authority"]
            with self.assertRaisesRegex(FamiliarViewError, "does not account for.*advisory_authority"):
                validate_view(view)


class ProvenanceTests(unittest.TestCase):
    """Schema validity does not prove the View represents an accepted revision."""

    def test_a_view_is_built_only_from_a_ref_the_store_resolves(self):
        with tempfile.TemporaryDirectory() as tmp:
            store, ref = stored(Path(tmp) / "familiars")
            forged = FamiliarRef(ref.id, ref.caster_id, ref.revision, "sha256:" + "0" * 64)
            with self.assertRaises(FamiliarStoreError):
                build_view(store, forged, policy="private", audience="bdo")

    def test_the_subject_block_names_the_revision_that_was_resolved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "familiars"
            store, first_ref = stored(root)
            store.put(familiar_candidate("a later attention"), caster_id="bdo")

            view = build_view(store, first_ref, policy="private", audience="bdo")

            self.assertEqual(1, view["subject"]["revision"])
            self.assertEqual(first_ref.digest, view["subject"]["digest"])
            self.assertEqual(["collapsed distinctions"], view["guidance"]["attention"])

    def test_a_view_of_an_older_revision_survives_a_newer_one(self):
        """The property #15's retention exists to make possible."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "familiars"
            store, accepted_ref = stored(root)
            accepted_view = build_view(store, accepted_ref, policy="private", audience="bdo")

            for index in range(3):
                store.put(familiar_candidate(f"revision {index + 2}"), caster_id="bdo")

            reopened = FamiliarStore(root)
            rebuilt = build_view(reopened, accepted_ref, policy="private", audience="bdo")
            self.assertEqual(accepted_view, rebuilt)


class RepresentationTests(unittest.TestCase):
    def test_dialect_is_represented_as_its_description(self):
        with tempfile.TemporaryDirectory() as tmp:
            store, ref = stored(Path(tmp) / "familiars")
            view = build_view(store, ref, policy="private", audience="bdo")
            self.assertEqual("Compact distinction-first working language.", view["guidance"]["dialect"])

    def test_a_view_does_not_share_mutable_state_with_the_store(self):
        with tempfile.TemporaryDirectory() as tmp:
            store, ref = stored(Path(tmp) / "familiars")
            view = build_view(store, ref, policy="private", audience="bdo")
            snapshot = deepcopy(view)
            view["guidance"]["attention"].append("mutated by a consumer")

            rebuilt = build_view(store, ref, policy="private", audience="bdo")
            self.assertEqual(snapshot, rebuilt)

    def test_building_refuses_a_category_that_is_not_source_guidance(self):
        with tempfile.TemporaryDirectory() as tmp:
            store, ref = stored(Path(tmp) / "familiars")
            with self.assertRaisesRegex(FamiliarViewError, "not a source guidance category"):
                build_view(store, ref, policy="host", audience="h", represent=["caster"])

    def test_building_requires_a_named_perspective(self):
        with tempfile.TemporaryDirectory() as tmp:
            store, ref = stored(Path(tmp) / "familiars")
            with self.assertRaisesRegex(FamiliarViewError, "policy"):
                build_view(store, ref, policy="", audience="bdo")
            with self.assertRaisesRegex(FamiliarViewError, "audience"):
                build_view(store, ref, policy="host", audience="")


if __name__ == "__main__":
    unittest.main()
