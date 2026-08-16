"""Executable correctness must not depend on composition symlinks (issue #17).

A checkout without symlink support writes an ordinary file containing the
target path where Git records a symlink. Any runtime path that traverses such
an entry fails there while succeeding on Linux, which makes the supported test
command platform dependent rather than portable.
"""

from __future__ import annotations

import json
import subprocess
import unittest

from kernel import resources
from kernel.resources import (
    CAST_SCHEMA,
    FAMILIAR_SCHEMA,
    FAMILIAR_VIEW_SCHEMA,
    OWL_PATH,
    REPO_ROOT,
    ResourceError,
    SPELL_SCHEMA,
    resource,
)

# The transitional composition symlinks this issue removes.
RETIRED_LINKS = ("format", "familiar", "owl")

CANONICAL_RESOURCES = {
    "SPELL_SCHEMA": SPELL_SCHEMA,
    "FAMILIAR_SCHEMA": FAMILIAR_SCHEMA,
    "FAMILIAR_VIEW_SCHEMA": FAMILIAR_VIEW_SCHEMA,
    "OWL_PATH": OWL_PATH,
    "CAST_SCHEMA": CAST_SCHEMA,
}


class CanonicalResourceTests(unittest.TestCase):
    def test_every_canonical_resource_exists_and_parses(self):
        for name, path in CANONICAL_RESOURCES.items():
            with self.subTest(resource=name):
                self.assertTrue(path.is_file(), f"{name} missing at {path}")
                json.loads(path.read_text(encoding="utf-8"))

    def test_canonical_resources_live_in_an_owned_domain(self):
        for name, path in CANONICAL_RESOURCES.items():
            with self.subTest(resource=name):
                relative = path.relative_to(REPO_ROOT)
                self.assertIn(relative.parts[0], resources.DOMAINS)

    def test_no_canonical_resource_traverses_a_retired_link(self):
        retired = [REPO_ROOT / "cast" / name for name in RETIRED_LINKS]
        for name, path in CANONICAL_RESOURCES.items():
            with self.subTest(resource=name):
                self.assertFalse(
                    any(link in path.parents for link in retired),
                    f"{name} resolves through a transitional composition link",
                )

    def test_retired_links_are_gone_from_the_cast_domain(self):
        for name in RETIRED_LINKS:
            with self.subTest(link=name):
                self.assertFalse(
                    (REPO_ROOT / "cast" / name).exists(),
                    f"cast/{name} is back; runtime resolution must not depend on it",
                )

    def test_resource_refuses_a_path_outside_the_owned_domains(self):
        with self.assertRaises(ResourceError):
            resource("docs", "anything.json")

    def test_resource_refuses_a_missing_path_by_name(self):
        with self.assertRaises(ResourceError) as caught:
            resource("spell", "format", "not-a-real-schema.json")
        self.assertIn("not-a-real-schema.json", str(caught.exception))

    def test_resource_resolves_a_real_canonical_path(self):
        self.assertEqual(SPELL_SCHEMA, resource("spell", "format", "spell.schema.json"))


class SymlinkFreeCheckoutTests(unittest.TestCase):
    """The repository must check out identically where symlinks are unsupported."""

    def test_no_tracked_file_is_recorded_as_a_symlink(self):
        try:
            listing = subprocess.run(
                ["git", "ls-files", "-s"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=True,
            ).stdout
        except (OSError, subprocess.CalledProcessError) as error:
            self.skipTest(f"git index unavailable: {error}")

        symlinks = [
            line.split("\t", 1)[-1]
            for line in listing.splitlines()
            if line.startswith("120000 ")
        ]
        self.assertEqual(
            [],
            symlinks,
            "tracked symlinks do not materialise on a checkout with core.symlinks=false",
        )


if __name__ == "__main__":
    unittest.main()
