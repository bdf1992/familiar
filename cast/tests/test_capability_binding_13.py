"""Requirements bind to exact capability receipts by typed demand (issue #13).

`compile_cast_plan()` matched each Requirement to the first receipt exposing
the requested operation string. An unrelated `write` capability could satisfy
`familiar-store-supported`, and the runtime had no way to express that a
numeric ceiling, a permission set, a Scope region, an Authority attenuation, a
protocol operation set, and a control boundary are six different relations
rather than six spellings of `>=`.
"""

from __future__ import annotations

import unittest

from practitioner import (
    CapabilityMatchError,
    CapabilityReceipt,
    Demand,
    Situation,
    compile_cast_plan,
)


def receipt(name, *, operations=("write",), environment="local", status="available",
            authority="bdo", locator="familiar-store", evidence="probe:ok",
            protocol=None, subject=None, capacity=None):
    return CapabilityReceipt(
        name=name,
        environment=environment,
        operations=tuple(operations),
        status=status,
        authority=authority,
        locator=locator,
        evidence=evidence,
        protocol=protocol,
        subject=subject,
        capacity=capacity or {},
    )


def situation(*receipts):
    return Situation(
        "situation-1",
        "session-1",
        {"id": "bdo", "kind": "human"},
        {"caster": "bdo"},
        ("local", "chat"),
        tuple(receipts),
        ("owl.system",),
    )


class SimpleCaseTests(unittest.TestCase):
    def test_a_bare_operation_name_still_binds_one_receipt(self):
        plan = compile_cast_plan(
            {"familiar-store-supported": "write"},
            situation(receipt("familiar persistence")),
        )
        self.assertTrue(plan.ready)
        self.assertEqual("familiar persistence", plan.requirements["familiar-store-supported"].name)

    def test_a_missing_mechanism_is_still_reported_as_a_gap(self):
        plan = compile_cast_plan({"familiar-store-supported": "write"}, situation())
        self.assertFalse(plan.ready)
        self.assertEqual(("capability-missing:familiar-store-supported:write",), plan.gaps)

    def test_an_unavailable_receipt_does_not_satisfy_a_demand(self):
        plan = compile_cast_plan(
            {"familiar-store-supported": "write"},
            situation(receipt("familiar persistence", status="degraded")),
        )
        self.assertFalse(plan.ready)


class IdentityConstraintTests(unittest.TestCase):
    """An unrelated receipt with the same operation no longer satisfies."""

    def test_wrong_capability_name_is_refused(self):
        plan = compile_cast_plan(
            {"familiar-store-supported": Demand(operation="write", capability="familiar persistence")},
            situation(receipt("scratch buffer")),
        )
        self.assertFalse(plan.ready)
        self.assertIn("capability-missing:familiar-store-supported:write", plan.gaps)

    def test_wrong_environment_is_refused(self):
        plan = compile_cast_plan(
            {"req": Demand(operation="write", environment="local")},
            situation(receipt("familiar persistence", environment="remote")),
        )
        self.assertFalse(plan.ready)

    def test_wrong_authority_is_refused(self):
        plan = compile_cast_plan(
            {"req": Demand(operation="write", authority="bdo")},
            situation(receipt("familiar persistence", authority="someone-else")),
        )
        self.assertFalse(plan.ready)

    def test_wrong_subject_is_refused(self):
        plan = compile_cast_plan(
            {"req": Demand(operation="write", subject="bdo.familiar")},
            situation(receipt("familiar persistence", subject="other.familiar")),
        )
        self.assertFalse(plan.ready)

    def test_wrong_protocol_is_refused(self):
        plan = compile_cast_plan(
            {"req": Demand(operation="write", protocol="familiar-store.v1")},
            situation(receipt("familiar persistence", protocol="familiar-store.v0")),
        )
        self.assertFalse(plan.ready)

    def test_wrong_locator_is_refused(self):
        plan = compile_cast_plan(
            {"req": Demand(operation="write", locator="familiar-store")},
            situation(receipt("familiar persistence", locator="chat-session")),
        )
        self.assertFalse(plan.ready)


class AmbiguityTests(unittest.TestCase):
    def test_two_admissible_receipts_fail_closed_rather_than_taking_the_first(self):
        plan = compile_cast_plan(
            {"req": "write"},
            situation(receipt("familiar persistence"), receipt("scratch buffer")),
        )
        self.assertFalse(plan.ready)
        self.assertEqual(
            ("capability-ambiguous:req:write:familiar persistence,scratch buffer",),
            plan.gaps,
        )
        self.assertNotIn("req", plan.matches)

    def test_enough_constraints_resolve_the_ambiguity_exactly(self):
        plan = compile_cast_plan(
            {"req": Demand(operation="write", capability="familiar persistence")},
            situation(receipt("familiar persistence"), receipt("scratch buffer")),
        )
        self.assertTrue(plan.ready)
        self.assertEqual("familiar persistence", plan.requirements["req"].name)


class CapacityRelationTests(unittest.TestCase):
    """Six relations, six different logics. None of them is `>=` in disguise."""

    def test_quota_compares_available_against_demanded(self):
        demand = Demand(operation="allocate", relation="quota", capacity={"demanded": 4})
        enough = situation(receipt("pool", operations=("allocate",), capacity={"available": 5}))
        short = situation(receipt("pool", operations=("allocate",), capacity={"available": 3}))

        self.assertTrue(compile_cast_plan({"req": demand}, enough).ready)
        self.assertFalse(compile_cast_plan({"req": demand}, short).ready)

    def test_permissions_requires_the_granted_set_to_cover_the_required_set(self):
        demand = Demand(
            operation="act",
            relation="permissions",
            capacity={"required": ("read", "write")},
        )
        covering = situation(receipt("acl", operations=("act",), capacity={"granted": ("read", "write", "list")}))
        partial = situation(receipt("acl", operations=("act",), capacity={"granted": ("read",)}))

        self.assertTrue(compile_cast_plan({"req": demand}, covering).ready)
        self.assertFalse(compile_cast_plan({"req": demand}, partial).ready)

    def test_scope_containment_runs_the_opposite_way_from_permissions(self):
        """A capability reaching further than the admissible region is refused."""
        demand = Demand(
            operation="mutate",
            relation="scope",
            capacity={"admissible": ("a.txt", "b.txt")},
        )
        contained = situation(receipt("fs view", operations=("mutate",), capacity={"region": ("a.txt",)}))
        wider = situation(receipt("fs view", operations=("mutate",), capacity={"region": ("a.txt", "c.txt")}))

        self.assertTrue(compile_cast_plan({"req": demand}, contained).ready)
        self.assertFalse(compile_cast_plan({"req": demand}, wider).ready)

    def test_authority_refuses_a_capability_granting_more_than_was_resolved(self):
        demand = Demand(
            operation="call",
            relation="authority",
            capacity={"resolved": ("familiar:read", "familiar:write")},
        )
        within = situation(receipt("token", operations=("call",), capacity={"grants": ("familiar:read",)}))
        broader = situation(receipt("token", operations=("call",), capacity={"grants": ("familiar:read", "registry:write")}))

        self.assertTrue(compile_cast_plan({"req": demand}, within).ready)
        self.assertFalse(compile_cast_plan({"req": demand}, broader).ready)

    def test_protocol_requires_the_provided_operations_to_cover_the_contract(self):
        demand = Demand(
            operation="speak",
            relation="protocol",
            capacity={"required_operations": ("put", "resolve")},
        )
        complete = situation(receipt("store api", operations=("speak",), capacity={"operations": ("put", "resolve", "list")}))
        incomplete = situation(receipt("store api", operations=("speak",), capacity={"operations": ("put",)}))

        self.assertTrue(compile_cast_plan({"req": demand}, complete).ready)
        self.assertFalse(compile_cast_plan({"req": demand}, incomplete).ready)

    def test_control_requires_the_mechanism_to_contain_the_named_boundary(self):
        demand = Demand(operation="run", relation="control", capacity={"boundary": "execution-timeout"})
        containing = situation(receipt("sandbox", operations=("run",), capacity={"contains": ("execution-timeout", "memory")}))
        not_containing = situation(receipt("sandbox", operations=("run",), capacity={"contains": ("memory",)}))

        self.assertTrue(compile_cast_plan({"req": demand}, containing).ready)
        self.assertFalse(compile_cast_plan({"req": demand}, not_containing).ready)

    def test_a_receipt_declaring_no_capacity_does_not_satisfy_a_capacity_demand(self):
        demand = Demand(operation="allocate", relation="quota", capacity={"demanded": 1})
        plan = compile_cast_plan({"req": demand}, situation(receipt("pool", operations=("allocate",))))
        self.assertFalse(plan.ready)

    def test_an_unknown_relation_is_an_expression_error_not_a_silent_gap(self):
        with self.assertRaisesRegex(CapabilityMatchError, "unknown capacity relation"):
            compile_cast_plan(
                {"req": Demand(operation="write", relation="vibes")},
                situation(receipt("familiar persistence")),
            )


class PlanEvidenceTests(unittest.TestCase):
    def test_the_plan_retains_the_exact_receipt_and_the_match_evidence(self):
        demand = Demand(operation="allocate", relation="quota", capacity={"demanded": 4})
        chosen = receipt("pool", operations=("allocate",), capacity={"available": 5})
        plan = compile_cast_plan({"req": demand}, situation(chosen))

        match = plan.matches["req"]
        self.assertEqual(chosen, match.receipt)
        self.assertEqual(demand, match.demand)
        self.assertEqual("quota", match.relation)
        self.assertEqual({"demanded": 4, "available": 5}, dict(match.detail))

    def test_scope_evidence_names_the_regions_that_decided_it(self):
        demand = Demand(operation="mutate", relation="scope", capacity={"admissible": ("a.txt", "b.txt")})
        plan = compile_cast_plan(
            {"req": demand},
            situation(receipt("fs view", operations=("mutate",), capacity={"region": ("a.txt",)})),
        )
        detail = dict(plan.matches["req"].detail)
        self.assertEqual(["a.txt", "b.txt"], detail["admissible"])
        self.assertEqual(["a.txt"], detail["region"])
        self.assertEqual([], detail["outside"])


class AttenuationTests(unittest.TestCase):
    def test_a_narrowing_demand_returns_an_attenuated_handle(self):
        demand = Demand(
            operation="mutate",
            relation="scope",
            capacity={"admissible": ("a.txt", "b.txt")},
            attenuate=True,
        )
        source = receipt("fs view", operations=("mutate",), capacity={"region": ("a.txt",)})
        plan = compile_cast_plan({"req": demand}, situation(source))

        match = plan.matches["req"]
        self.assertTrue(match.attenuated)
        self.assertEqual(source, match.receipt)
        self.assertEqual(("a.txt",), plan.handle("req").capacity["region"])
        self.assertNotEqual(plan.handle("req"), source)

    def test_an_attenuated_quota_handle_carries_only_what_was_demanded(self):
        demand = Demand(operation="allocate", relation="quota", capacity={"demanded": 4}, attenuate=True)
        plan = compile_cast_plan(
            {"req": demand},
            situation(receipt("pool", operations=("allocate",), capacity={"available": 9})),
        )
        self.assertEqual(4, plan.handle("req").capacity["available"])
        self.assertEqual(9, plan.matches["req"].receipt.capacity["available"])

    def test_an_attenuated_authority_handle_drops_grants_beyond_the_resolution(self):
        demand = Demand(
            operation="call",
            relation="authority",
            capacity={"resolved": ("familiar:read", "familiar:write")},
            attenuate=True,
        )
        plan = compile_cast_plan(
            {"req": demand},
            situation(receipt("token", operations=("call",), capacity={"grants": ("familiar:read",)})),
        )
        self.assertEqual(("familiar:read",), plan.handle("req").capacity["grants"])

    def test_a_relation_with_no_narrowing_rule_refuses_rather_than_widening(self):
        demand = Demand(operation="run", relation="control", capacity={"boundary": "execution-timeout"}, attenuate=True)
        plan = compile_cast_plan(
            {"req": demand},
            situation(receipt("sandbox", operations=("run",), capacity={"contains": ("execution-timeout",)})),
        )
        self.assertFalse(plan.ready)
        self.assertEqual(("attenuation-unavailable:req:control",), plan.gaps)
        self.assertNotIn("req", plan.matches)

    def test_a_non_narrowing_demand_hands_through_the_receipt_itself(self):
        source = receipt("familiar persistence")
        plan = compile_cast_plan({"req": "write"}, situation(source))
        self.assertFalse(plan.matches["req"].attenuated)
        self.assertEqual(source, plan.handle("req"))


class DemandExpressionTests(unittest.TestCase):
    def test_an_empty_demand_is_refused_at_expression_time(self):
        for bad in ("", None, 7):
            with self.subTest(demand=bad):
                with self.assertRaises(CapabilityMatchError):
                    compile_cast_plan({"req": bad}, situation(receipt("familiar persistence")))

    def test_a_quota_demand_without_an_integer_is_refused_at_expression_time(self):
        with self.assertRaisesRegex(CapabilityMatchError, "integer 'demanded'"):
            compile_cast_plan(
                {"req": Demand(operation="allocate", relation="quota", capacity={"demanded": "four"})},
                situation(receipt("pool", operations=("allocate",), capacity={"available": 5})),
            )


if __name__ == "__main__":
    unittest.main()
