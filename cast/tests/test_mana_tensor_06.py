from __future__ import annotations

import unittest

from environment.mana_tensor import (
    AxisMarker,
    ManaCoordinate,
    ManaTensor,
    ManaTensorError,
    ManaTerm,
)


class ManaTensor06Tests(unittest.TestCase):
    def make_cast_tensor(self, cast_id: str, components: list[tuple[str, int]]) -> ManaTensor:
        tensor = ManaTensor.genesis(20, runtime="runtime-1", locality="network")
        ambient = ManaCoordinate(
            runtime="runtime-1",
            locality="network",
            disposition="ambient",
            relation="ambient",
        )
        for component, amount in components:
            committed = ManaCoordinate(
                spell="workspace-tidy",
                effect="tidy",
                component=component,
                caster="bdo",
                situation=f"situation-{cast_id}",
                cast=cast_id,
                runtime="runtime-1",
                locality="network",
                phase="during",
                disposition="committed",
                relation="participates",
                provenance=f"plan:{cast_id}:{component}",
            )
            tensor = tensor.transition(ambient, committed, amount)
        return tensor

    def test_genesis_is_one_conserved_ambient_relation(self):
        tensor = ManaTensor.genesis(20, runtime="runtime-1", locality="network")
        self.assertEqual(20, tensor.contract())
        self.assertEqual(20, tensor.contract(disposition="ambient"))
        self.assertEqual(0, tensor.contract(disposition="committed"))

    def test_cost_is_scalar_contraction_of_unique_composition(self):
        tensor_a = self.make_cast_tensor(
            "cast-a",
            [
                ("target-resolution", 2),
                ("authority-binding", 1),
                ("scope-containment", 3),
                ("technique-execution", 6),
                ("consequence-evidence", 3),
            ],
        )
        tensor_b = self.make_cast_tensor(
            "cast-b",
            [
                ("target-resolution", 1),
                ("material-component", 4),
                ("familiar-participation", 1),
                ("technique-execution", 4),
                ("duration-binding", 2),
                ("consequence-evidence", 3),
            ],
        )

        self.assertEqual(15, tensor_a.cast_cost("cast-a"))
        self.assertEqual(15, tensor_b.cast_cost("cast-b"))
        self.assertNotEqual(
            tensor_a.composition(cast="cast-a"),
            tensor_b.composition(cast="cast-b"),
        )
        self.assertEqual(20, tensor_a.contract())
        self.assertEqual(20, tensor_b.contract())

    def test_component_projection_preserves_contributing_relation(self):
        tensor = self.make_cast_tensor(
            "cast-a",
            [("scope-containment", 3), ("technique-execution", 12)],
        )
        scope = tensor.project(cast="cast-a", component="scope-containment")
        self.assertEqual(1, len(scope))
        self.assertEqual(3, scope[0].amount)
        self.assertEqual("committed", scope[0].coordinate.disposition)
        self.assertEqual("participates", scope[0].coordinate.relation)

    def test_unknown_and_not_applicable_are_distinct_coordinates(self):
        unresolved = ManaCoordinate(caster=AxisMarker.UNKNOWN, relation="claim")
        ambient = ManaCoordinate(caster=AxisMarker.NOT_APPLICABLE, relation="ambient")
        self.assertNotEqual(unresolved, ambient)
        self.assertTrue(unresolved.matches(caster=AxisMarker.UNKNOWN))
        self.assertFalse(unresolved.matches(caster=AxisMarker.NOT_APPLICABLE))

    def test_transition_moves_relation_without_changing_total(self):
        tensor = ManaTensor.genesis(10, runtime="runtime-1", locality="network")
        ambient = ManaCoordinate(
            runtime="runtime-1",
            locality="network",
            disposition="ambient",
            relation="ambient",
        )
        claim = ManaCoordinate(
            caster="bdo",
            runtime="runtime-1",
            locality="network",
            disposition="claimed",
            relation="claim",
        )
        tensor = tensor.transition(ambient, claim, 4)
        self.assertEqual(10, tensor.contract())
        self.assertEqual(6, tensor.contract(disposition="ambient"))
        self.assertEqual(4, tensor.contract(caster="bdo", disposition="claimed"))

    def test_tensor_refuses_unaccounted_or_created_mana(self):
        coordinate = ManaCoordinate(
            runtime="runtime-1",
            locality="network",
            disposition="ambient",
            relation="ambient",
        )
        with self.assertRaisesRegex(ManaTensorError, "conservation violated"):
            ManaTensor(10, (ManaTerm(coordinate, 9),))
        with self.assertRaisesRegex(ManaTensorError, "conservation violated"):
            ManaTensor(10, (ManaTerm(coordinate, 11),))

    def test_transition_refuses_more_than_exact_source_contains(self):
        tensor = ManaTensor.genesis(10, runtime="runtime-1", locality="network")
        ambient = ManaCoordinate(
            runtime="runtime-1",
            locality="network",
            disposition="ambient",
            relation="ambient",
        )
        claim = ManaCoordinate(
            caster="bdo",
            runtime="runtime-1",
            locality="network",
            disposition="claimed",
            relation="claim",
        )
        with self.assertRaisesRegex(ManaTensorError, "insufficient Mana"):
            tensor.transition(ambient, claim, 11)


if __name__ == "__main__":
    unittest.main()
