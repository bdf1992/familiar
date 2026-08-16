"""Consequence classification and compensation for effects the world keeps.

The invariant casting law can observe and classify local mutations. External
systems cannot generally be undone: a successful HTTP call, a sent message, a
charged card. Without an explicit model a failed postcondition collapses three
materially different outcomes into one:

```text
nothing happened
something happened and was exactly undone
something happened and the world still has it
```

The third is not a worse version of the second. It is a different fact, and a
runtime that cannot say which one occurred cannot be trusted about either.

Four findings, and `compensatable` is not a promise that compensation will
work -- only that a path exists:

```text
none           no effectful consequence observed
reversed       exact mutation, restoration independently verified
residual       persistent mutation, no compensation path declared
compensatable  persistent mutation with a declared compensation path
```

**Compensation is a new consequence-bearing operation, not deletion of
history.** It produces its own attributable record linked to the original. The
original CAST keeps its consequence and its residual whether compensation
succeeds, fails, or is never attempted.

**A provider may not certify its own rollback.** An inverse-looking API is not
evidence that state was restored, so a `reversed` finding requires an observer
distinct from the executor -- the same independence rule settlement already
uses in `environment/magic.py`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

NONE = "none"
REVERSED = "reversed"
RESIDUAL = "residual"
COMPENSATABLE = "compensatable"

CONSEQUENCE_KINDS = (NONE, REVERSED, RESIDUAL, COMPENSATABLE)

#: A finding that leaves the world changed. Both retain a residual on CAST.
PERSISTENT_KINDS = (RESIDUAL, COMPENSATABLE)

SUCCEEDED = "succeeded"
FAILED = "failed"
REFUSED = "refused"


class ConsequenceError(ValueError):
    """A consequence finding or compensation path could not be expressed."""


@dataclass(frozen=True)
class ConsequenceFinding:
    """What the Environment observed about the world after execution.

    `observer` is the identity that produced the finding. It is required for
    `reversed` and must differ from the executor, because "I undid it" from the
    thing that did it is an assertion rather than an observation.
    """

    kind: str
    observer: str
    detail: Mapping[str, Any] = field(default_factory=dict)
    #: Names the compensation path when kind is `compensatable`.
    compensation: str | None = None

    def __post_init__(self) -> None:
        if self.kind not in CONSEQUENCE_KINDS:
            raise ConsequenceError(f"unknown consequence kind: {self.kind}")
        if not isinstance(self.observer, str) or not self.observer:
            raise ConsequenceError("a consequence finding requires an observer")
        if self.kind == COMPENSATABLE and not self.compensation:
            raise ConsequenceError("a compensatable finding must name its compensation path")
        if self.kind != COMPENSATABLE and self.compensation:
            raise ConsequenceError(
                f"{self.kind} declares a compensation path; only compensatable may"
            )

    @property
    def persistent(self) -> bool:
        return self.kind in PERSISTENT_KINDS

    def as_dict(self) -> dict[str, Any]:
        described = {"kind": self.kind, "observer": self.observer, "detail": dict(self.detail)}
        if self.compensation is not None:
            described["compensation"] = self.compensation
        return described


def verify_reversal(finding: ConsequenceFinding, executor_id: str) -> None:
    """Refuse a rollback claim the executor made about itself."""
    if finding.kind == REVERSED and finding.observer == executor_id:
        raise ConsequenceError(
            "exact reversal requires an observer independent of the executor; "
            f"{executor_id!r} cannot certify its own rollback"
        )


@dataclass(frozen=True)
class CompensationPath:
    """A declared way to compensate one kind of persistent consequence."""

    id: str
    provider: str
    compensate: Callable[[Mapping[str, Any]], Any]

    def __post_init__(self) -> None:
        for name in ("id", "provider"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                raise ConsequenceError(f"a compensation path requires {name}")
        if not callable(self.compensate):
            raise ConsequenceError("a compensation path requires a callable")


@dataclass(frozen=True)
class CompensationRecord:
    """A separate attributable event linked to the original Cast.

    It never edits the original. A reader holding both sees what happened and
    what was done about it, in that order, which is the only honest shape when
    the first event is real and the second may have failed.
    """

    id: str
    original_cast_id: str
    path_id: str
    provider: str
    status: str
    original_finding: Mapping[str, Any]
    detail: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "compensation_id": self.id,
            "original_cast_id": self.original_cast_id,
            "path": self.path_id,
            "provider": self.provider,
            "status": self.status,
            "original_finding": dict(self.original_finding),
            "detail": dict(self.detail),
        }


def compensate(
    cast_record: Mapping[str, Any],
    finding: ConsequenceFinding,
    path: CompensationPath,
    context: Mapping[str, Any] | None = None,
    *,
    compensation_id: str | None = None,
) -> CompensationRecord:
    """Attempt compensation and return a new record. Never edits the original.

    A failure is a recorded outcome rather than an exception, because "we tried
    and could not undo it" is exactly the fact the caller needs to keep.
    """
    if finding.kind != COMPENSATABLE:
        return CompensationRecord(
            id=compensation_id or f"compensation-of-{cast_record['cast_id']}",
            original_cast_id=cast_record["cast_id"],
            path_id=path.id,
            provider=path.provider,
            status=REFUSED,
            original_finding=finding.as_dict(),
            detail={"reason": f"consequence is {finding.kind}, not compensatable"},
        )
    if finding.compensation != path.id:
        return CompensationRecord(
            id=compensation_id or f"compensation-of-{cast_record['cast_id']}",
            original_cast_id=cast_record["cast_id"],
            path_id=path.id,
            provider=path.provider,
            status=REFUSED,
            original_finding=finding.as_dict(),
            detail={"reason": f"finding names path {finding.compensation!r}, not {path.id!r}"},
        )

    try:
        result = path.compensate(dict(context or {}))
    except Exception as exc:
        return CompensationRecord(
            id=compensation_id or f"compensation-of-{cast_record['cast_id']}",
            original_cast_id=cast_record["cast_id"],
            path_id=path.id,
            provider=path.provider,
            status=FAILED,
            original_finding=finding.as_dict(),
            detail={"error": f"{type(exc).__name__}: {exc}"},
        )

    return CompensationRecord(
        id=compensation_id or f"compensation-of-{cast_record['cast_id']}",
        original_cast_id=cast_record["cast_id"],
        path_id=path.id,
        provider=path.provider,
        status=SUCCEEDED,
        original_finding=finding.as_dict(),
        detail={"result": result},
    )
