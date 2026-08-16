import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from validation.candidate_adapter import load_candidate_spell
from validation.casting_04 import cast_with_binding, validate_technique_binding

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "workspace-tidy"


def load_host_module():
    spec = importlib.util.spec_from_file_location("workspace_tidy_host_04", EXAMPLE / "host.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_binding():
    with (EXAMPLE / "technique-binding.0.4-draft.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)


class WorkspaceTidyCasting04Tests(unittest.TestCase):
    def setUp(self):
        self.host_module = load_host_module()
        self.spell = load_candidate_spell(EXAMPLE / "SPELL.0.3-candidate.md")
        self.binding = load_binding()
        validate_technique_binding(self.binding)

    def make_workspace(self, root: Path) -> None:
        # write_bytes, not write_text: this workspace is observed and hashed by
        # the host. This test does not currently compare against a checked-in
        # record, so it passes on Windows today -- but it shares the hazard with
        # test_workspace_tidy_integration and would acquire the same defect the
        # moment a digest assertion is added. Byte-exact fixtures are the
        # invariant, not a workaround.
        (root / "notes.txt").write_bytes(b"authored\n")
        (root / "cache.agentspells-disposable").write_bytes(b"cache\n")
        nested = root / "build"
        nested.mkdir()
        (nested / "artifact.agentspells-disposable").write_bytes(b"artifact\n")
        (nested / "keep.json").write_bytes(b'{"keep":true}\n')

    def test_real_skill_casts_through_04_binding_and_keeps_spell_postconditions(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            self.make_workspace(workspace)
            notes_before = (workspace / "notes.txt").read_bytes()
            keep_before = (workspace / "build" / "keep.json").read_bytes()
            host = self.host_module.WorkspaceTidyHost(
                workspace,
                write_authorized_casters={"ci-agent"},
            )

            record = cast_with_binding(
                host.kernel(),
                self.spell,
                self.binding,
                effect_id="tidy",
                caster={"id": "ci-agent", "kind": "agent"},
                target=str(workspace),
                cast_id="cast-workspace-tidy-04",
            )

            self.assertEqual("closed", record["closure"]["decision"])
            self.assertEqual("resolved", record["outcome"])
            self.assertEqual("workspace-tidy-skill", record["technique"]["id"])
            self.assertEqual(1, host.executor_calls)
            self.assertFalse((workspace / "cache.agentspells-disposable").exists())
            self.assertFalse((workspace / "build" / "artifact.agentspells-disposable").exists())
            self.assertEqual(notes_before, (workspace / "notes.txt").read_bytes())
            self.assertEqual(keep_before, (workspace / "build" / "keep.json").read_bytes())

            requirements = {(item["id"], item["phase"], item["status"]) for item in record["observations"] if item["kind"] == "requirement"}
            self.assertIn(("write-authority", "before", "satisfied"), requirements)
            self.assertIn(("execution-time", "during", "satisfied"), requirements)
            self.assertIn(("disposable-absent", "after", "satisfied"), requirements)
            self.assertIn(("preserve-unmarked", "after", "satisfied"), requirements)

    def test_real_skill_refuses_before_execution_when_binding_drops_duration_support(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            self.make_workspace(workspace)
            host = self.host_module.WorkspaceTidyHost(
                workspace,
                write_authorized_casters={"ci-agent"},
            )
            binding = json.loads(json.dumps(self.binding))
            binding["mechanisms"]["duration"] = []

            record = cast_with_binding(
                host.kernel(),
                self.spell,
                binding,
                effect_id="tidy",
                caster={"id": "ci-agent", "kind": "agent"},
                target=str(workspace),
            )

            self.assertEqual("refused", record["closure"]["decision"])
            self.assertEqual(0, host.executor_calls)
            self.assertTrue((workspace / "cache.agentspells-disposable").exists())
            self.assertTrue(any("binding-duration-containment-missing" in reason for reason in record["closure"]["reasons"]))


if __name__ == "__main__":
    unittest.main()
