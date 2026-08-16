from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any


class CastSessionError(ValueError):
    pass


_STATES = {
    "invoked",
    "preparing",
    "awaiting_mark",
    "ready_to_close",
    "closed",
    "executing",
    "observing",
    "resolved",
    "failed",
}


@dataclass
class CastSession:
    """Resumable pre-closure state for practitioner-in-the-loop Techniques.

    Draft candidates may change while preparing. No effect artifact may be
    committed until the practitioner explicitly accepts a candidate and the
    session is closed.
    """

    cast_id: str
    spell: str
    effect: str
    caster: dict[str, Any]
    target: Any
    state: str = "invoked"
    current: dict[str, Any] | None = None
    marks: list[str] = field(default_factory=list)
    accepted: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.state not in _STATES:
            raise CastSessionError(f"invalid cast session state: {self.state}")

    def begin_preparation(self) -> None:
        self._require("invoked")
        self.state = "preparing"

    def propose(self, candidate: dict[str, Any]) -> None:
        if self.state not in {"preparing", "awaiting_mark"}:
            raise CastSessionError("candidate can only be proposed while preparing")
        self.current = deepcopy(candidate)
        self.state = "awaiting_mark"

    def mark(self, mark: str) -> None:
        self._require("awaiting_mark")
        if not isinstance(mark, str) or not mark.strip():
            raise CastSessionError("mark must be non-empty")
        self.marks.append(mark.strip())
        self.state = "preparing"

    def accept(self) -> dict[str, Any]:
        self._require("awaiting_mark")
        if self.current is None:
            raise CastSessionError("no candidate to accept")
        self.accepted = deepcopy(self.current)
        self.state = "ready_to_close"
        return deepcopy(self.accepted)

    def close(self) -> None:
        self._require("ready_to_close")
        if self.accepted is None:
            raise CastSessionError("closure requires an accepted candidate")
        self.state = "closed"

    def begin_execution(self) -> None:
        self._require("closed")
        self.state = "executing"

    def begin_observation(self) -> None:
        self._require("executing")
        self.state = "observing"

    def resolve(self) -> None:
        self._require("observing")
        self.state = "resolved"

    def fail(self) -> None:
        if self.state == "resolved":
            raise CastSessionError("resolved session cannot fail")
        self.state = "failed"

    def _require(self, expected: str) -> None:
        if self.state != expected:
            raise CastSessionError(f"expected {expected}, got {self.state}")
