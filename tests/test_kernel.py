import json
import unittest
from pathlib import Path

from kernel.spell_kernel import SpellKernel, load_spell_md, validate_cast_record, validate_familiar

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures"


def familiar(name):
    with (FIX / name).open("r", encoding="utf-8") as f:
        return json.load(f)


def observer(phase, context):
    if phase == "before":
        return {"value": {"temp": ["a.tmp"], "authored_changed": False}, "source": "fixture", "freshness_ms": 0}
    return {"value": {"temp": [], "authored_changed": False}, "source": "fixture", "freshness_ms": 0}


def target_observable(phase, context):
    return context.get("target") == "fixture-workspace"


def tidy_confirmed(phase, context):
    after = context.get("telemetry_after", {}).get("workspace-state", {})
    return after.get("value", {}).get("temp") == []


def preserve_authored(phase, context):
    bucket = "telemetry" if phase == "before" else "telemetry_after"
    state = context.get(bucket, {}).get("workspace-state", {})
    return state.get("value", {}).get("authored_changed") is False


def authority(caster, permission, context):
    return permission == "workspace.write" and caster.get("id") in {"caster-1", "agent-1"}


def execute(spell, effect_id, context):
    return {"removed": ["a.tmp"]}


def guide(fam, spell, effect_id, context):
    return {"dialect": fam["dialect"]["description"], "attention": fam["attention"]}


def kernel(executor=execute, authority_resolver=authority):
    return SpellKernel(observers={"workspace-state": observer}, requirements={"target-observable": target_observable, "tidy-confirmed": tidy_confirmed}, limits={"preserve-authored": preserve_authored}, authority_resolver=authority_resolver, executor=executor, guide=guide)


class KernelTests(unittest.TestCase):
    def setUp(self):
        self.spell = load_spell_md(FIX / "SPELL.md")

    def test_kernel_closes_and_resolves(self):
        record = kernel().cast(self.spell, effect_id="tidy", caster={"id": "caster-1", "kind": "human"}, target="fixture-workspace")
        self.assertEqual("closed", record["closure"]["decision"])
        self.assertEqual("resolved", record["outcome"])
        validate_cast_record(record)

    def test_kernel_refuses_to_close_without_authority(self):
        record = kernel(authority_resolver=lambda caster, permission, context: False).cast(self.spell, effect_id="tidy", caster={"id": "caster-1", "kind": "human"}, target="fixture-workspace")
        self.assertEqual("refused", record["closure"]["decision"])
        self.assertIsNone(record["outcome"])
        self.assertTrue(any("authority-denied" in reason for reason in record["closure"]["reasons"]))

    def test_malformed_familiar_is_rejected(self):
        broken = familiar("familiar-casual.json")
        del broken["dialect"]
        record = kernel().cast(self.spell, effect_id="tidy", caster={"id": "caster-1", "kind": "human"}, target="fixture-workspace", familiar=broken)
        self.assertEqual("refused", record["closure"]["decision"])
        self.assertTrue(any("familiar-invalid" in reason for reason in record["closure"]["reasons"]))

    def test_two_familiars_change_guidance_not_spell_behavior(self):
        first = kernel().cast(self.spell, effect_id="tidy", caster={"id": "caster-1", "kind": "human"}, target="fixture-workspace", familiar=familiar("familiar-casual.json"), cast_id="cast-a")
        second = kernel().cast(self.spell, effect_id="tidy", caster={"id": "agent-1", "kind": "agent"}, target="fixture-workspace", familiar=familiar("familiar-json.json"), cast_id="cast-b")
        self.assertNotEqual(first["guidance"], second["guidance"])
        self.assertEqual(first["closure"]["decision"], second["closure"]["decision"])
        self.assertEqual(first["outcome"], second["outcome"])
        self.assertEqual(first["result"], second["result"])

    def test_failed_execution_keeps_record_and_residual(self):
        def fail(spell, effect_id, context):
            raise RuntimeError("fixture failure")
        record = kernel(executor=fail).cast(self.spell, effect_id="tidy", caster={"id": "caster-1", "kind": "human"}, target="fixture-workspace")
        self.assertEqual("closed", record["closure"]["decision"])
        self.assertEqual("failed", record["outcome"])
        self.assertTrue(record["residuals"])
        self.assertTrue(any(o["kind"] == "telemetry" and o["phase"] == "after" for o in record["observations"]))

    def test_machine_caster_with_json_familiar_receives_machine_record(self):
        machine = familiar("familiar-json.json")
        validate_familiar(machine)
        record = kernel().cast(self.spell, effect_id="tidy", caster={"id": "agent-1", "kind": "agent"}, target="fixture-workspace", familiar=machine)
        decoded = json.loads(json.dumps(record))
        self.assertEqual("resolved", decoded["outcome"])
        self.assertEqual("agent", decoded["caster"]["kind"])
        self.assertEqual("agent-1-json", decoded["familiar"]["id"])


if __name__ == "__main__":
    unittest.main()
