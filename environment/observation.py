"""Environment-owned raw observation evidence for issue #35.

Observation is evidence, not authority. This module records what an independent
observer could or could not see and preserves conflicting observations without
choosing a winner. Cast owns how those records are evaluated against a sealed
Runtime Obligation / EvidenceContract; the Environment owns the observation
identity, provenance, and explicit unknown/unavailable states.

The shared independence predicate here is deliberately small. Different domains
retain their own refusal messages and policy, but they no longer need different
definitions of the elementary relation:

    observer is independent iff it is a named principal distinct from every
    named principal whose claim/action it is supposed to observe.

Role/organization trust beyond identity remains consumer policy; this is not a
PKI or a universal trust theorem.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Mapping


OBSERVED = "observed"
UNKNOWN = "unknown"
UNAVAILABLE = "unavailable"
OBSERVATION_STATUSES = frozenset({OBSERVED, UNKNOWN, UNAVAILABLE})


class ObservationError(ValueError):
    """Raw observation evidence is malformed or would overwrite prior evidence."""


def observer_is_independent(observer: str | None, *principals: str | None) -> bool:
    """Return whether `observer` is distinct from every named principal.

    Empty/unknown observer identity is never independent. Empty principals are
    ignored because there is no identity to compare against; callers decide
    whether an absent principal is itself an expression error.
    """

    if not isinstance(observer, str) or not observer:
        return False
    prohibited = {
        principal
        for principal in principals
        if isinstance(principal, str) and principal
    }
    return observer not in prohibited


@dataclass(frozen=True)
class EnvironmentObservation:
    """One attributable raw observation for one Cast topic.

    `topic` is an address, not an interpretation. For #35 it is commonly a
    Runtime Obligation id or `consequence`. Multiple observations may address
    the same topic and disagree; the journal retains all of them.

    `UNKNOWN` means an observer was present but the value could not be
    determined. `UNAVAILABLE` means the observation mechanism could not produce
    evidence. Neither is converted to false/zero/absence.
    """

    id: str
    cast_id: str
    topic: str
    observer: str
    provenance: str
    status: str
    value: Any = None
    detail: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("id", "cast_id", "topic", "observer", "provenance"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise ObservationError(f"observation requires {name}")
        if self.status not in OBSERVATION_STATUSES:
            raise ObservationError(
                f"observation status must be one of {sorted(OBSERVATION_STATUSES)}"
            )
        if not isinstance(self.detail, Mapping):
            raise ObservationError("observation detail must be a mapping")

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "cast_id": self.cast_id,
            "topic": self.topic,
            "observer": self.observer,
            "provenance": self.provenance,
            "status": self.status,
            "value": deepcopy(self.value),
            "detail": deepcopy(dict(self.detail)),
        }


class ObservationJournal:
    """Append-only in-memory raw evidence journal for one Environment host.

    The journal is intentionally minimal and does not claim durable storage.
    Duplicate ids are refused rather than overwritten, including when a later
    observer would prefer a different value.
    """

    def __init__(self) -> None:
        self._records: list[EnvironmentObservation] = []
        self._ids: set[str] = set()

    def append(self, observation: EnvironmentObservation) -> None:
        if not isinstance(observation, EnvironmentObservation):
            raise ObservationError("journal accepts EnvironmentObservation values")
        if observation.id in self._ids:
            raise ObservationError(f"observation id already recorded: {observation.id}")
        self._records.append(observation)
        self._ids.add(observation.id)

    def for_cast(self, cast_id: str, topic: str | None = None) -> tuple[EnvironmentObservation, ...]:
        if not isinstance(cast_id, str) or not cast_id:
            raise ObservationError("cast_id must be a non-empty string")
        if topic is not None and (not isinstance(topic, str) or not topic):
            raise ObservationError("topic must be a non-empty string when supplied")
        return tuple(
            record
            for record in self._records
            if record.cast_id == cast_id and (topic is None or record.topic == topic)
        )

    @property
    def records(self) -> tuple[EnvironmentObservation, ...]:
        return tuple(self._records)
