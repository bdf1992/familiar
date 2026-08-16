"""An accepted FamiliarRef stays resolvable to the exact artifact it names (issue #15).

A Familiar View represents one exact accepted revision. While the store kept
only the latest revision per Familiar id, writing revision N+1 destroyed the
bytes revision N named, and every long-lived reference to N failed as stale
after ordinary Familiar evolution.
"""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from familiar.store import (
    FamiliarRef,
    FamiliarStore,
    FamiliarStoreError,
    RevisionNotRetained,
)


def familiar_candidate(attention: str = "collapsed distinctions") -> dict:
    return {
        "familiar_format": "0.3",
        "id": "bdo.familiar",
        "caster": {"id": "bdo", "kind": "human"},
        "dialect": {"description": "Compact distinction-first working language."},
        "attention": [attention],
        "preferences": ["small inspectable kernels"],
        "stake": ["practitioner agent work"],
        "advisory_authority": [],
    }


def revision_files(root: Path) -> list[Path]:
    return sorted(root.rglob("r*.json"))


class RevisionRetentionTests(unittest.TestCase):
    def test_both_revisions_resolve_to_their_exact_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = FamiliarStore(Path(tmp) / "familiars")
            first = familiar_candidate("first attention")
            second = familiar_candidate("second attention")

            ref_one = store.put(first, caster_id="bdo")
            ref_two = store.put(second, caster_id="bdo")

            self.assertEqual(1, ref_one.revision)
            self.assertEqual(2, ref_two.revision)
            self.assertNotEqual(ref_one.digest, ref_two.digest)
            self.assertEqual(first, store.resolve(ref_one))
            self.assertEqual(second, store.resolve(ref_two))

    def test_writing_a_new_revision_does_not_touch_the_earlier_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "familiars"
            store = FamiliarStore(root)
            store.put(familiar_candidate("first attention"), caster_id="bdo")
            [first_file] = revision_files(root)
            before = first_file.read_bytes()

            store.put(familiar_candidate("second attention"), caster_id="bdo")

            self.assertEqual(before, first_file.read_bytes())
            self.assertEqual(2, len(revision_files(root)))

    def test_both_revisions_survive_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "familiars"
            first = familiar_candidate("first attention")
            second = familiar_candidate("second attention")
            writer = FamiliarStore(root)
            ref_one = writer.put(first, caster_id="bdo")
            ref_two = writer.put(second, caster_id="bdo")

            reopened = FamiliarStore(root)
            self.assertEqual(first, reopened.resolve(ref_one))
            self.assertEqual(second, reopened.resolve(ref_two))

    def test_an_older_ref_still_resolves_after_a_newer_revision_exists(self):
        """The property a long-lived Familiar View depends on."""
        with tempfile.TemporaryDirectory() as tmp:
            store = FamiliarStore(Path(tmp) / "familiars")
            accepted = familiar_candidate("the accepted revision")
            ref = store.put(accepted, caster_id="bdo")
            for index in range(5):
                store.put(familiar_candidate(f"later revision {index}"), caster_id="bdo")

            self.assertEqual(accepted, store.resolve(ref))
            self.assertEqual(6, store.retention("bdo.familiar").latest)

    def test_exact_resolution_never_silently_upgrades_to_latest(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = FamiliarStore(Path(tmp) / "familiars")
            first = familiar_candidate("first attention")
            ref_one = store.put(first, caster_id="bdo")
            store.put(familiar_candidate("second attention"), caster_id="bdo")

            self.assertEqual(first, store.resolve(ref_one))

            latest_ref, latest_value = store.resolve_latest("bdo.familiar")
            self.assertEqual(2, latest_ref.revision)
            self.assertEqual(["second attention"], latest_value["attention"])
            self.assertNotEqual(ref_one, latest_ref)


class RevisionTamperTests(unittest.TestCase):
    def test_each_revision_is_tamper_checked_independently(self):
        for target in (0, 1):
            with self.subTest(tampered_revision=target + 1):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp) / "familiars"
                    store = FamiliarStore(root)
                    refs = [
                        store.put(familiar_candidate("first attention"), caster_id="bdo"),
                        store.put(familiar_candidate("second attention"), caster_id="bdo"),
                    ]
                    files = revision_files(root)
                    envelope = json.loads(files[target].read_text(encoding="utf-8"))
                    envelope["familiar"]["attention"].append("tampered")
                    files[target].write_text(json.dumps(envelope), encoding="utf-8")

                    reopened = FamiliarStore(root)
                    with self.assertRaises(FamiliarStoreError):
                        reopened.resolve(refs[target])
                    # The untouched revision remains resolvable.
                    intact = 1 - target
                    self.assertIsInstance(reopened.resolve(refs[intact]), dict)

    def test_a_forged_ref_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = FamiliarStore(Path(tmp) / "familiars")
            ref = store.put(familiar_candidate(), caster_id="bdo")

            forgeries = {
                "revision": FamiliarRef(ref.id, ref.caster_id, 99, ref.digest),
                "digest": FamiliarRef(ref.id, ref.caster_id, ref.revision, "sha256:" + "0" * 64),
                "caster": FamiliarRef(ref.id, "not-bdo", ref.revision, ref.digest),
                "id": FamiliarRef("someone.else", ref.caster_id, ref.revision, ref.digest),
            }
            for field, forged in forgeries.items():
                with self.subTest(forged=field):
                    with self.assertRaises(FamiliarStoreError):
                        store.resolve(forged)

    def test_a_corrupt_manifest_does_not_defeat_exact_resolution(self):
        """The manifest is a convenience index. The revision files are the truth."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "familiars"
            store = FamiliarStore(root)
            first = familiar_candidate("first attention")
            ref_one = store.put(first, caster_id="bdo")
            store.put(familiar_candidate("second attention"), caster_id="bdo")

            [manifest] = list(root.rglob("manifest.json"))
            manifest.unlink()

            reopened = FamiliarStore(root)
            self.assertEqual(first, reopened.resolve(ref_one))
            self.assertEqual(2, reopened.retention("bdo.familiar").latest)


class LegacyStoreMigrationTests(unittest.TestCase):
    """A latest-only store is adopted without inventing history it never had."""

    def _write_legacy_entry(self, root: Path, familiar: dict, revision: int) -> None:
        from familiar.store import _digest, _legacy_file_key

        root.mkdir(parents=True, exist_ok=True)
        (root / _legacy_file_key(familiar["id"])).write_text(
            json.dumps(
                {
                    "id": familiar["id"],
                    "revision": revision,
                    "digest": _digest(familiar),
                    "familiar": familiar,
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )

    def test_the_retained_legacy_revision_still_resolves(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "familiars"
            legacy = familiar_candidate("written by the old store")
            self._write_legacy_entry(root, legacy, revision=4)

            from familiar.store import _digest

            store = FamiliarStore(root)
            ref = FamiliarRef("bdo.familiar", "bdo", 4, _digest(legacy))
            self.assertEqual(legacy, store.resolve(ref))

    def test_revisions_the_old_store_never_kept_are_reported_as_not_retained(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "familiars"
            legacy = familiar_candidate("written by the old store")
            self._write_legacy_entry(root, legacy, revision=4)

            from familiar.store import _digest

            store = FamiliarStore(root)
            retention = store.retention("bdo.familiar")
            self.assertEqual(4, retention.latest)
            self.assertEqual(4, retention.earliest_retained)
            self.assertTrue(retention.migrated_from_latest_only)

            with self.assertRaises(RevisionNotRetained) as caught:
                store.resolve(FamiliarRef("bdo.familiar", "bdo", 2, _digest(legacy)))
            self.assertIn("never retained", str(caught.exception))

    def test_writing_after_migration_continues_the_revision_sequence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "familiars"
            legacy = familiar_candidate("written by the old store")
            self._write_legacy_entry(root, legacy, revision=4)

            from familiar.store import _digest

            store = FamiliarStore(root)
            new_ref = store.put(familiar_candidate("written after migration"), caster_id="bdo")
            self.assertEqual(5, new_ref.revision)

            reopened = FamiliarStore(root)
            self.assertEqual(legacy, reopened.resolve(FamiliarRef("bdo.familiar", "bdo", 4, _digest(legacy))))
            self.assertEqual(
                ["written after migration"],
                reopened.resolve(new_ref)["attention"],
            )


class InMemoryStoreTests(unittest.TestCase):
    def test_revisions_are_retained_without_a_root(self):
        store = FamiliarStore()
        first = familiar_candidate("first attention")
        second = familiar_candidate("second attention")
        ref_one = store.put(first, caster_id="bdo")
        ref_two = store.put(second, caster_id="bdo")

        self.assertEqual(first, store.resolve(ref_one))
        self.assertEqual(second, store.resolve(ref_two))


if __name__ == "__main__":
    unittest.main()
