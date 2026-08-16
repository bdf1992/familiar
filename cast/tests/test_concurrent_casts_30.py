"""Concurrent Cast isolation and conflict semantics (issue #30).

Two Practitioners may resolve overlapping targets, close against the same
pre-state, then execute concurrently and invalidate one another's assumptions.
Closure evidence goes stale between admission and commit, and the failure mode
is a lost update that nothing reports.
"""

from __future__ import annotations

import unittest

from practitioner.concurrency import (
    COMMITTED,
    CONFLICT,
    EXCLUSIVE,
    SHARED,
    CastAttempt,
    ConcurrencyError,
    ReservationLedger,
    StateVersion,
    VersionedStore,
    replan,
    version_of,
)


def store():
    return VersionedStore({"ledger": ["opening"], "index": {"count": 0}})


class StateIdentityTests(unittest.TestCase):
    """What a CastPlan must retain for conflict detection to be possible."""

    def test_a_state_version_requires_both_resource_and_version(self):
        for bad in ({"resource": "", "version": "v"}, {"resource": "r", "version": ""}):
            with self.subTest(**bad):
                with self.assertRaisesRegex(ConcurrencyError, "requires"):
                    StateVersion(**bad)

    def test_a_version_changes_when_the_value_changes(self):
        self.assertEqual(version_of(["a"]), version_of(["a"]))
        self.assertNotEqual(version_of(["a"]), version_of(["a", "b"]))

    def test_reading_hands_out_the_current_version(self):
        subject = store()
        value, version = subject.read("ledger")
        self.assertEqual(["opening"], value)
        self.assertEqual(version_of(["opening"]), version.version)

    def test_a_resource_name_alone_cannot_detect_a_conflict(self):
        """Two attempts naming the same resource are not thereby in conflict."""
        subject = store()
        first = CastAttempt("attempt-1", subject.observe("ledger"))
        second = CastAttempt("attempt-2", subject.observe("ledger"))
        # Same resource, same observed version, no mutation between them.
        self.assertEqual(first.observed, second.observed)
        self.assertTrue(subject.commit(first, {}).committed)


class OptimisticConcurrencyTests(unittest.TestCase):
    """Two Casts over overlapping state. Reference strategy, end to end."""

    def test_at_most_one_commit_succeeds_against_the_same_pre_state(self):
        subject = store()
        first = CastAttempt("attempt-1", subject.observe("ledger"))
        second = CastAttempt("attempt-2", subject.observe("ledger"))

        first_result = subject.commit(first, {"ledger": ["opening", "from-first"]})
        second_result = subject.commit(second, {"ledger": ["opening", "from-second"]})

        self.assertTrue(first_result.committed)
        self.assertFalse(second_result.committed)
        self.assertEqual(CONFLICT, second_result.status)
        # The first Cast's consequence survives. Nothing was silently overwritten.
        self.assertEqual(["opening", "from-first"], subject.value("ledger"))

    def test_a_conflict_names_the_resource_and_both_versions(self):
        subject = store()
        stale = CastAttempt("attempt-1", subject.observe("ledger"))
        subject.commit(CastAttempt("attempt-0", subject.observe("ledger")), {"ledger": ["moved"]})

        result = subject.commit(stale, {"ledger": ["too-late"]})

        self.assertEqual(CONFLICT, result.status)
        [finding] = result.conflicts
        self.assertEqual("ledger", finding.resource)
        self.assertEqual(version_of(["opening"]), finding.observed)
        self.assertEqual(version_of(["moved"]), finding.current)
        self.assertEqual("attempt-1", result.attempt_id)

    def test_a_conflict_on_any_observed_resource_refuses_the_whole_commit(self):
        """A partial apply would be the lost update this exists to prevent."""
        subject = store()
        attempt = CastAttempt("attempt-1", subject.observe("ledger", "index"))
        subject.commit(CastAttempt("other", subject.observe("index")), {"index": {"count": 1}})

        result = subject.commit(attempt, {"ledger": ["changed"], "index": {"count": 99}})

        self.assertEqual(CONFLICT, result.status)
        self.assertEqual(["opening"], subject.value("ledger"))
        self.assertEqual({"count": 1}, subject.value("index"))

    def test_non_overlapping_casts_both_commit(self):
        subject = store()
        first = CastAttempt("attempt-1", subject.observe("ledger"))
        second = CastAttempt("attempt-2", subject.observe("index"))

        self.assertTrue(subject.commit(first, {"ledger": ["a"]}).committed)
        self.assertTrue(subject.commit(second, {"index": {"count": 5}}).committed)


class RetryTests(unittest.TestCase):
    def test_retrying_creates_a_new_attempt_with_fresh_evidence(self):
        subject = store()
        stale = CastAttempt("attempt-1", subject.observe("ledger"))
        subject.commit(CastAttempt("winner", subject.observe("ledger")), {"ledger": ["winner"]})
        self.assertEqual(CONFLICT, subject.commit(stale, {"ledger": ["loser"]}).status)

        retry = replan(subject, stale, "attempt-2")

        self.assertEqual("attempt-2", retry.attempt_id)
        self.assertNotEqual(stale.observed, retry.observed)
        self.assertEqual(version_of(["winner"]), retry.observed[0].version)
        result = subject.commit(retry, {"ledger": ["winner", "retried"]})
        self.assertTrue(result.committed)
        self.assertEqual(["winner", "retried"], subject.value("ledger"))

    def test_a_conflict_is_not_resumable_under_its_old_identity(self):
        subject = store()
        attempt = CastAttempt("attempt-1", subject.observe("ledger"))
        with self.assertRaisesRegex(ConcurrencyError, "not resumable"):
            replan(subject, attempt, "attempt-1")


class ReservationTests(unittest.TestCase):
    """Pessimistic strategy, and deadlock avoidance by total order."""

    def test_an_exclusive_reservation_excludes_another_holder(self):
        ledger = ReservationLedger()
        self.assertTrue(ledger.acquire("cast-a", ["ledger"]))
        self.assertFalse(ledger.acquire("cast-b", ["ledger"]))
        self.assertEqual("cast-a", ledger.held_by("ledger"))

        ledger.release("cast-a", ["ledger"])
        self.assertTrue(ledger.acquire("cast-b", ["ledger"]))

    def test_shared_reservations_coexist_and_exclude_an_exclusive_one(self):
        ledger = ReservationLedger()
        self.assertTrue(ledger.acquire("reader-a", ["ledger"], SHARED))
        self.assertTrue(ledger.acquire("reader-b", ["ledger"], SHARED))
        self.assertFalse(ledger.acquire("writer", ["ledger"], EXCLUSIVE))

        ledger.release("reader-a", ["ledger"])
        # One reader remains, so the writer still waits.
        self.assertFalse(ledger.acquire("writer", ["ledger"], EXCLUSIVE))
        ledger.release("reader-b", ["ledger"])
        self.assertTrue(ledger.acquire("writer", ["ledger"], EXCLUSIVE))

    def test_multi_resource_acquisition_follows_one_total_order(self):
        ledger = ReservationLedger()
        self.assertEqual(("a", "b", "c"), ledger.acquisition_order(["c", "a", "b"]))
        self.assertEqual(("a", "b"), ledger.acquisition_order(["b", "a", "b"]))

    def test_the_classic_deadlock_pair_cannot_deadlock(self):
        """Two holders wanting {a,b} and {b,a}: one gets both, the other is refused."""
        ledger = ReservationLedger()
        first = ledger.acquire("cast-a", ["alpha", "beta"])
        second = ledger.acquire("cast-b", ["beta", "alpha"])

        self.assertTrue(first)
        self.assertFalse(second)
        # No partial hold: the loser holds nothing, so nobody waits behind it.
        self.assertEqual("cast-a", ledger.held_by("alpha"))
        self.assertEqual("cast-a", ledger.held_by("beta"))

    def test_a_refused_acquisition_leaves_no_partial_hold(self):
        ledger = ReservationLedger()
        ledger.acquire("cast-a", ["beta"])
        self.assertFalse(ledger.acquire("cast-b", ["alpha", "beta"]))
        # 'alpha' was never taken, so a third Cast can still have it.
        self.assertIsNone(ledger.held_by("alpha"))
        self.assertTrue(ledger.acquire("cast-c", ["alpha"]))

    def test_reacquiring_what_you_already_hold_is_not_a_conflict(self):
        ledger = ReservationLedger()
        self.assertTrue(ledger.acquire("cast-a", ["alpha"]))
        self.assertTrue(ledger.acquire("cast-a", ["alpha", "beta"]))

    def test_an_unknown_mode_is_refused(self):
        with self.assertRaisesRegex(ConcurrencyError, "unknown reservation mode"):
            ReservationLedger().acquire("cast-a", ["alpha"], "maybe")


class EndToEndTests(unittest.TestCase):
    def test_pessimistic_reservation_prevents_the_conflict_optimism_detects(self):
        """The same overlap, under both strategies, with different failure shapes."""
        subject = store()
        ledger = ReservationLedger()

        # Pessimistic: the second Cast never closes, so no work is wasted.
        self.assertTrue(ledger.acquire("cast-a", ["ledger"]))
        self.assertFalse(ledger.acquire("cast-b", ["ledger"]))

        # Optimistic: both close, both execute, the second is refused at commit.
        first = CastAttempt("attempt-1", subject.observe("ledger"))
        second = CastAttempt("attempt-2", subject.observe("ledger"))
        self.assertTrue(subject.commit(first, {"ledger": ["a"]}).committed)
        self.assertEqual(CONFLICT, subject.commit(second, {"ledger": ["b"]}).status)

        # Either way exactly one consequence landed and the refusal is visible.
        self.assertEqual(["a"], subject.value("ledger"))

    def test_commit_result_is_recordable_as_cast_evidence(self):
        subject = store()
        stale = CastAttempt("attempt-1", subject.observe("ledger"))
        subject.commit(CastAttempt("winner", subject.observe("ledger")), {"ledger": ["w"]})
        result = subject.commit(stale, {"ledger": ["l"]})

        described = result.as_dict()
        self.assertEqual(CONFLICT, described["status"])
        self.assertEqual("attempt-1", described["attempt_id"])
        self.assertEqual("ledger", described["conflicts"][0]["resource"])

    def test_committing_an_unknown_resource_is_an_expression_error(self):
        subject = store()
        attempt = CastAttempt("attempt-1", subject.observe("ledger"))
        with self.assertRaisesRegex(ConcurrencyError, "unknown resource"):
            subject.commit(attempt, {"nowhere": 1})


if __name__ == "__main__":
    unittest.main()
