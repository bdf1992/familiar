import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from kernel.spell_kernel import load_spell_md


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "workspace-tidy"


def load_host_module():
    spec = importlib.util.spec_from_file_location("workspace_tidy_host", EXAMPLE / "host.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class WorkspaceTidyIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.host_module = load_host_module()
        self.spell = load_spell_md(EXAMPLE / "SPELL.md")

    def make_workspace(self, root: Path) -> None:
        (root / "notes.txt").write_text("authored\n", encoding="utf-8")
        (root / "cache.agentspells-disposable").write_text("cache\n", encoding="utf-8")
        nested = root / "build"
        nested.mkdir()
        (nested / "artifact.agentspells-disposable").write_text("artifact\n", encoding="utf-8")
        (nested / "keep.json").write_text('{"keep":true}\n', encoding="utf-8")

    def test_skill_technique_produces_observed_external_effect(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            self.make_workspace(workspace)
            notes_before = (workspace / "notes.txt").read_bytes()
            keep_before = (workspace / "build" / "keep.json").read_bytes()

            host = self.host_module.WorkspaceTidyHost(
                workspace,
                write_authorized_casters={"ci-agent"},
            )
            record = host.kernel().cast(
                self.spell,
                effect_id="tidy",
                caster={"id": "ci-agent", "kind": "agent"},
                target=str(workspace),
                cast_id="cast-workspace-tidy-integration",
            )

            self.assertEqual("closed", record["closure"]["decision"])
            self.assertEqual("resolved", record["outcome"])
            self.assertEqual(1, host.executor_calls)
            self.assertFalse((workspace / "cache.agentspells-disposable").exists())
            self.assertFalse((workspace / "build" / "artifact.agentspells-disposable").exists())
            self.assertEqual(notes_before, (workspace / "notes.txt").read_bytes())
            self.assertEqual(keep_before, (workspace / "build" / "keep.json").read_bytes())
            self.assertEqual([], record["residuals"])
            json.dumps(record)

            postcondition = [
                item for item in record["observations"]
                if item["kind"] == "requirement" and item["id"] == "disposable-absent"
            ]
            self.assertEqual("satisfied", postcondition[-1]["status"])

            expected = json.loads((EXAMPLE / "CAST.example.json").read_text(encoding="utf-8"))
            self.assertEqual(expected, record)

    def test_denied_authority_refuses_before_technique_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            self.make_workspace(workspace)
            host = self.host_module.WorkspaceTidyHost(
                workspace,
                write_authorized_casters=set(),
            )

            record = host.kernel().cast(
                self.spell,
                effect_id="tidy",
                caster={"id": "ci-agent", "kind": "agent"},
                target=str(workspace),
                cast_id="cast-workspace-tidy-denied",
            )

            self.assertEqual("refused", record["closure"]["decision"])
            self.assertIsNone(record["outcome"])
            self.assertEqual(0, host.executor_calls)
            self.assertTrue((workspace / "cache.agentspells-disposable").exists())
            self.assertIn("authority-denied: workspace.write", record["closure"]["reasons"])


if __name__ == "__main__":
    unittest.main()
