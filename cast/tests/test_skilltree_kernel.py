"""Skill-neutral collection/build kernel receiving tests."""

from __future__ import annotations

import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator

from skilltree import Build, Collection, SkillTreeError


ROOT = Path(__file__).resolve().parents[2]


def collection_data() -> dict:
    return {
        "collection_id": "collection:owl-work",
        "version": "0.1.0",
        "skills": [
            {
                "id": "skill:inspect",
                "title": "Inspect",
                "point_cost": 1,
                "requires": [],
                "artifact": {"adapter": "agent-skill/v1", "locator": "skills/inspect"},
                "lesson_refs": ["lesson:observe-before-changing"],
            },
            {
                "id": "skill:compute",
                "title": "Compute",
                "point_cost": 1,
                "requires": ["skill:inspect"],
                "artifact": {"adapter": "spell/v0.2", "locator": "spells/compute"},
            },
            {
                "id": "skill:mutate",
                "title": "Mutate",
                "point_cost": 2,
                "requires": ["skill:compute"],
                "artifact": {"adapter": "opaque/v1", "locator": "repo://mutate"},
            },
            {
                "id": "skill:attest",
                "title": "Attest",
                "point_cost": 2,
                "requires": ["skill:inspect", "skill:compute"],
                "artifact": {"adapter": "soveraeign-skill/v1", "locator": "skill://attest"},
            },
        ],
    }


class SkillTreeKernelTests(unittest.TestCase):
    def test_collection_schema_accepts_the_kernel_fixture(self):
        schema = json.loads((ROOT / "skilltree" / "collection.schema.json").read_text("utf-8"))
        Draft202012Validator(schema).validate(collection_data())

    def test_collection_accepts_multiple_artifact_formats_without_interpreting_them(self):
        collection = Collection.from_mapping(collection_data())
        self.assertEqual(
            {"agent-skill/v1", "spell/v0.2", "opaque/v1", "soveraeign-skill/v1"},
            {node.artifact.adapter for node in collection.skills.values()},
        )

    def test_unknown_prerequisite_refuses_the_collection(self):
        data = collection_data()
        data["skills"][1]["requires"] = ["skill:missing"]
        with self.assertRaisesRegex(SkillTreeError, "unknown prerequisites"):
            Collection.from_mapping(data)

    def test_prerequisite_cycle_refuses_the_collection(self):
        data = collection_data()
        data["skills"][0]["requires"] = ["skill:compute"]
        with self.assertRaisesRegex(SkillTreeError, "cycle"):
            Collection.from_mapping(data)

    def test_unlock_refuses_before_prerequisites_without_mutating_build(self):
        collection = Collection.from_mapping(collection_data())
        build = collection.new_build(4)
        with self.assertRaisesRegex(SkillTreeError, "missing prerequisites"):
            collection.unlock(build, "skill:compute")
        self.assertEqual((), build.unlocked)

    def test_unlock_spends_points_and_emits_immutable_transition_receipt(self):
        collection = Collection.from_mapping(collection_data())
        build = collection.new_build(4)
        first = collection.unlock(build, "skill:inspect")
        second = collection.unlock(first.after, "skill:compute")
        self.assertEqual(build, first.before)
        self.assertEqual(("skill:inspect", "skill:compute"), second.after.unlocked)
        self.assertEqual(2, collection.spent_points(second.after))
        self.assertEqual(1, second.points_spent)

    def test_unlock_refuses_when_point_budget_is_insufficient(self):
        collection = Collection.from_mapping(collection_data())
        build = collection.unlock(collection.new_build(2), "skill:inspect").after
        build = collection.unlock(build, "skill:compute").after
        with self.assertRaisesRegex(SkillTreeError, "insufficient skill points"):
            collection.unlock(build, "skill:mutate")

    def test_build_is_bound_to_an_exact_collection_revision(self):
        collection = Collection.from_mapping(collection_data())
        foreign = Build(collection.id, "0.2.0", collection.revision, 10)
        with self.assertRaisesRegex(SkillTreeError, "different collection revision"):
            collection.unlock(foreign, "skill:inspect")

    def test_build_refuses_same_version_with_changed_collection_content(self):
        original = Collection.from_mapping(collection_data())
        changed_data = collection_data()
        changed_data["skills"][0]["point_cost"] = 2
        changed = Collection.from_mapping(changed_data)
        self.assertNotEqual(original.revision, changed.revision)
        with self.assertRaisesRegex(SkillTreeError, "different collection revision"):
            changed.unlock(original.new_build(10), "skill:inspect")

    def test_tree_is_a_projection_and_shared_node_identity_can_repeat(self):
        collection = Collection.from_mapping(collection_data())
        tree = collection.project_tree()
        inspect = tree[0]
        compute = next(child for child in inspect["children"] if child["id"] == "skill:compute")
        self.assertIn("skill:attest", {child["id"] for child in inspect["children"]})
        self.assertIn("skill:attest", {child["id"] for child in compute["children"]})

    def test_lesson_reference_does_not_unlock_or_reduce_cost(self):
        collection = Collection.from_mapping(collection_data())
        node = collection.skills["skill:inspect"]
        self.assertEqual(("lesson:observe-before-changing",), node.lesson_refs)
        build = collection.new_build(0)
        with self.assertRaisesRegex(SkillTreeError, "insufficient skill points"):
            collection.unlock(build, node.id)


if __name__ == "__main__":
    unittest.main()
