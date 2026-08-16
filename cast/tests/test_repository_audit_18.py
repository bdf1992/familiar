"""The repository audit must describe the tree it claims to cover (issue #18).

`AGENTS.md` instructs agents to consult `REPOSITORY_AUDIT.md` before
architectural changes, so a stale audit is itself misleading repository state.
The previous audit predated the 0.6 Magic runtime, the Familiar View surface,
and every repository governance file, and nothing detected that.

This turns completeness into a mechanical property. It does not check that any
row is *correct* -- a purpose or lifecycle claim is a judgment no test can make
-- only that no tracked file is missing and no inventoried path has vanished.
"""

from __future__ import annotations

from pathlib import Path
import re
import subprocess
import unittest

# Derived here rather than imported, so this check does not depend on #17.
REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIT = REPO_ROOT / "REPOSITORY_AUDIT.md"


def tracked_files() -> list[str]:
    listing = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return [line for line in listing.splitlines() if line]


def cited_paths(text: str) -> set[str]:
    """Every backticked token that looks like a repository path."""
    return {
        token
        for token in re.findall(r"`([^`\n]+)`", text)
        if "/" in token or "." in token
    }


class AuditCompletenessTests(unittest.TestCase):
    def setUp(self):
        try:
            self.tracked = tracked_files()
        except (OSError, subprocess.CalledProcessError) as error:
            self.skipTest(f"git index unavailable: {error}")
        self.text = AUDIT.read_text(encoding="utf-8")
        self.cited = cited_paths(self.text)

    def test_every_tracked_file_is_inventoried(self):
        missing = sorted(path for path in self.tracked if path not in self.cited)
        self.assertEqual(
            [],
            missing,
            "tracked files absent from REPOSITORY_AUDIT.md:\n  " + "\n  ".join(missing),
        )

    def test_no_inventoried_path_has_vanished_from_the_tree(self):
        tracked = set(self.tracked)
        directories = {
            parent
            for path in tracked
            for parent in (str(Path(path).parent).replace("\\", "/"),)
            if parent != "."
        }
        stale = sorted(
            path
            for path in self.cited
            if "/" in path
            and path not in tracked
            and path.rstrip("/") not in directories
            and "*" not in path
            and " " not in path
        )
        self.assertEqual(
            [],
            stale,
            "paths inventoried by REPOSITORY_AUDIT.md that no longer exist:\n  " + "\n  ".join(stale),
        )

    def test_the_audit_records_the_commit_and_ci_run_it_rests_on(self):
        """A current-state claim with no attributable evidence is a claim, not an audit."""
        self.assertRegex(self.text, r"Audited commit\D+[0-9a-f]{7,40}")
        self.assertRegex(self.text, r"actions/runs/\d+")


if __name__ == "__main__":
    unittest.main()
