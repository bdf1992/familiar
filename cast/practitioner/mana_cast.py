"""Integrate the invariant Cast crossing with conserved Mana (issue #16).

This Work seam begins before #73 Closure so it can prove the #16 ordering law:

    exact open plan
    -> verify pre-existing Claim and commit capacity
    -> independently observed Brink
    -> Closure
    -> Claimed -> Committed exactly once
    -> effectful executor attempt exactly once
    -> Environment-owned consequence verification
    -> settlement

It reuses `environment.magic.MagicRuntime`; there is no second Cast-Mana state
machine here.

Compatible subset
-----------------
The current MagicRuntime stores one commitment per `cast_id`. This first
integration therefore supports exactly one sealed `ManaParticipation` for a
Mana-bearing Cast. Multiple participants/localities are not flattened into one
scalar commitment; richer relational commitment remains future #26/runtime work.

Within this subset `ManaParticipation.claim` is the minimum *pre-existing Claim
basis* that the participant must already hold at the sealed locality. Casting
does not call `MagicRuntime.claim()`. `commit` is the exact quantity allowed to
cross from Claimed to Committed after Closure.

The deterministic Mana cast id is derived from the immutable ClosedPlan digest,
so replaying the same closed attempt reaches MagicRuntime's existing cast-id
replay guard before any executor call.

This module is not CAST sealing. It returns an integration receipt that #36 may
later carry into the immutable CAST record.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Callable, Mapping

from environment.magic import MagicRuntime, MagicRuntimeError, ManaEvent

from .brink_closure import (
    EnvironmentBrinkProbe,
    OpenPlanAttachment,
    observe_and_close,
    verify_open_plan_attachment,
)
from .crossing import ClosedPlan, ManaParticipation, plan_digest


class ManaCastError(ValueError):
    """The Cast cannot preserve its sealed Mana or lifecycle invariants."""


@dataclass(frozen=True)
class ManaAdmission:
    """Read-only pre-Closure evidence that the sealed commitment is admissible."""

    participant: str
    locality: str
    claim_basis: int
    commit: int
    observed_claimed: int
    observed_committed_total: int
    max_cast: int
    max_committed: int
    total_mana: int


@dataclass(frozen=True)
class ExecutionAttempt:
    """Executor result, distinct from Environment consequence."""

    succeeded: bool
    result: Any = None
    error_type: str | None = None
    error_message: str | None = None


@dataclass(frozen=True)
class ManaCastResult:
    """Evidence from one #16 integration attempt; not the final CAST record."""

    closed_plan: ClosedPlan
    cast_id: str
    admission: ManaAdmission
    commit_event: ManaEvent
    execution: ExecutionAttempt
    settlement_event: ManaEvent | None
    settlement_error: str | None
    total_before: int
    total_after: int

    @property
    def settled(self) -> bool:
        return self.settlement_event is not None and self.settlement_error is None


Executor = Callable[[ClosedPlan, str], Any]


def _active_committed_total(runtime: MagicRuntime) -> int:
    """Project active committed Mana from the public immutable event history."""

    active: dict[str, int] = {}
    for event in runtime.events:
        if event.operation == "commit":
            cast_id = event.details.get("cast_id")
            if isinstance(cast_id, str):
                active[cast_id] = event.amount
        elif event.operation == "settle":
            cast_id = event.details.get("cast_id")
            if isinstance(cast_id, str):
                active.pop(cast_id, None)
    return sum(active.values())


def _single_participation(attachment: OpenPlanAttachment) -> ManaParticipation:
    if not isinstance(attachment, OpenPlanAttachment):
        raise ManaCastError("Mana integration requires exact OpenPlanAttachment")
    participation = attachment.plan.mana
    if len(participation) != 1:
        raise ManaCastError(
            "first Cast-Mana integration supports exactly one ManaParticipation; "
            "multiple participants/localities must not be flattened"
        )
    item = participation[0]
    if item.claim <= 0 or item.commit <= 0:
        raise ManaCastError(
            "Mana-bearing Cast requires positive claim basis and positive commit; "
            "zero-Mana semantics are outside #16"
        )
    return item


def admit_mana_before_closure(
    attachment: OpenPlanAttachment,
    situation_view: Mapping[str, Any],
    runtime: MagicRuntime,
) -> ManaAdmission:
    """Check the sealed Claim basis and commit ceilings without moving Mana.

    This is deliberately before Brink/Closure. It does not call `claim` or
    `commit`. The actual transition is still performed atomically by
    `MagicRuntime.commit()` after Closure, which repeats its own authoritative
    access/capacity/replay checks.
    """

    if not isinstance(runtime, MagicRuntime):
        raise ManaCastError("Mana integration requires MagicRuntime")
    verify_open_plan_attachment(attachment, situation_view)
    participation = _single_participation(attachment)

    claimed = runtime.claimed_by(participation.participant, locality=participation.locality)
    committed_total = _active_committed_total(runtime)

    if claimed < participation.claim:
        raise ManaCastError(
            f"insufficient pre-existing Claim: required {participation.claim}, observed {claimed}"
        )
    if participation.commit > runtime.limits.max_cast:
        raise ManaCastError(
            f"planned commit {participation.commit} exceeds max_cast {runtime.limits.max_cast}"
        )
    if committed_total + participation.commit > runtime.limits.max_committed:
        raise ManaCastError(
            "planned commit exceeds remaining max_committed capacity"
        )
    if runtime.total() != runtime.total_mana:
        raise ManaCastError("Mana conservation is already violated before Closure")

    return ManaAdmission(
        participant=participation.participant,
        locality=participation.locality,
        claim_basis=participation.claim,
        commit=participation.commit,
        observed_claimed=claimed,
        observed_committed_total=committed_total,
        max_cast=runtime.limits.max_cast,
        max_committed=runtime.limits.max_committed,
        total_mana=runtime.total_mana,
    )


def _verify_admission_still_holds(admission: ManaAdmission, runtime: MagicRuntime) -> None:
    """Detect Claim/capacity drift between pre-Closure admission and commitment."""

    claimed = runtime.claimed_by(admission.participant, locality=admission.locality)
    committed_total = _active_committed_total(runtime)
    if claimed < admission.claim_basis:
        raise ManaCastError(
            "pre-existing Claim changed after admission and before commitment"
        )
    if admission.commit > runtime.limits.max_cast:
        raise ManaCastError("max_cast changed after admission and before commitment")
    if committed_total + admission.commit > runtime.limits.max_committed:
        raise ManaCastError(
            "max_committed capacity changed after admission and before commitment"
        )
    if runtime.total() != admission.total_mana:
        raise ManaCastError("conserved Mana total changed across Closure")


def mana_cast_id(closed: ClosedPlan) -> str:
    """Replay identity for Mana participation, derived from immutable Closure."""

    if not isinstance(closed, ClosedPlan):
        raise ManaCastError("Mana cast id requires ClosedPlan")
    actual = plan_digest(closed.plan)
    if closed.digest != actual:
        raise ManaCastError("ClosedPlan digest does not match its immutable plan")
    if not closed.brink.at_brink:
        raise ManaCastError("Mana cannot commit from a ClosedPlan without a clean Brink")
    return f"closed-plan:{closed.digest}"


def _attempt_execution(executor: Executor, closed: ClosedPlan, cast_id: str) -> ExecutionAttempt:
    if not callable(executor):
        raise ManaCastError("executor must be callable")
    try:
        return ExecutionAttempt(succeeded=True, result=deepcopy(executor(closed, cast_id)))
    except Exception as error:  # noqa: BLE001 -- failure remains evidence; settlement still runs
        return ExecutionAttempt(
            succeeded=False,
            error_type=type(error).__name__,
            error_message=str(error),
        )


def settle_mana_cast(closed: ClosedPlan, runtime: MagicRuntime) -> ManaEvent:
    """Retry settlement only; never re-execute the Technique."""

    cast_id = mana_cast_id(closed)
    return runtime.settle(cast_id)


def run_mana_cast(
    attachment: OpenPlanAttachment,
    situation_view: Mapping[str, Any],
    runtime: MagicRuntime,
    *,
    effect_probe: EnvironmentBrinkProbe | None,
    mana_probe: EnvironmentBrinkProbe | None,
    executor: Executor,
) -> ManaCastResult:
    """Run the #16 ordering law through settlement when evidence is available.

    Commit failures propagate and occur before the executor. Executor failures
    are captured rather than raised because Environment consequence still needs
    to be observed and settled. Settlement failure is recorded while leaving
    the conserved commitment live for `settle_mana_cast`; rerunning this whole
    function cannot repeat the effect because the deterministic cast id is
    already consumed by MagicRuntime's commit replay guard.
    """

    total_before = runtime.total()
    admission = admit_mana_before_closure(attachment, situation_view, runtime)

    closed = observe_and_close(
        attachment,
        situation_view,
        effect_probe=effect_probe,
        mana_probe=mana_probe,
    )
    _verify_admission_still_holds(admission, runtime)
    cast_id = mana_cast_id(closed)

    # This is the first Mana state transition attributable to this Cast.
    commit_event = runtime.commit(
        cast_id,
        admission.participant,
        admission.locality,
        admission.commit,
    )

    # Effectful execution is ordered strictly after successful commitment.
    execution = _attempt_execution(executor, closed, cast_id)

    settlement_event: ManaEvent | None = None
    settlement_error: str | None = None
    try:
        settlement_event = runtime.settle(cast_id)
    except MagicRuntimeError as error:
        # Missing/unconfirmed consequence evidence leaves Mana Committed. The
        # effect is never retried by this result; settlement can be retried only
        # through `settle_mana_cast` when independent evidence becomes available.
        settlement_error = f"{type(error).__name__}: {error}"

    total_after = runtime.total()
    if total_after != total_before or total_after != runtime.total_mana:
        raise ManaCastError("Mana conservation changed across Cast integration")

    return ManaCastResult(
        closed_plan=closed,
        cast_id=cast_id,
        admission=admission,
        commit_event=commit_event,
        execution=execution,
        settlement_event=settlement_event,
        settlement_error=settlement_error,
        total_before=total_before,
        total_after=total_after,
    )
