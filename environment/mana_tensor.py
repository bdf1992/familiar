from __future__ import annotations

from dataclasses import dataclass, fields, replace
from enum import Enum
from typing import Iterable


class ManaTensorError(ValueError):
    pass


class AxisMarker(str, Enum):
    """Explicit non-value states for a Mana coordinate.

    NOT_APPLICABLE means the relation has no value on this axis. UNKNOWN means
    the axis participates but the runtime has not resolved its value. They are
    deliberately distinct.
    """

    NOT_APPLICABLE = "not-applicable"
    UNKNOWN = "unknown"


AxisValue = str | AxisMarker


def _axis(value: AxisValue, name: str) -> None:
    if isinstance(value, AxisMarker):
        return
    if not isinstance(value, str) or not value:
        raise ManaTensorError(f"Mana axis {name} must be a non-empty string or AxisMarker")


def _amount(value: int, name: str = "amount") -> None:
    # Python bool is an int subclass; Mana quantities deliberately are not.
    if type(value) is not int or value <= 0:
        raise ManaTensorError(f"{name} must be a positive integer")


@dataclass(frozen=True, order=True)
class ManaCoordinate:
    """One sparse coordinate in situated Mana tensor logic.

    These axes are intentionally runtime relations, not portable SPELL.md
    fields. A coordinate may omit an axis because it is not applicable, or mark
    it unknown when the relation requires a value that is not yet resolved.
    """

    spell: AxisValue = AxisMarker.NOT_APPLICABLE
    effect: AxisValue = AxisMarker.NOT_APPLICABLE
    component: AxisValue = AxisMarker.NOT_APPLICABLE
    caster: AxisValue = AxisMarker.NOT_APPLICABLE
    situation: AxisValue = AxisMarker.NOT_APPLICABLE
    cast: AxisValue = AxisMarker.NOT_APPLICABLE
    runtime: AxisValue = AxisMarker.NOT_APPLICABLE
    locality: AxisValue = AxisMarker.NOT_APPLICABLE
    phase: AxisValue = AxisMarker.NOT_APPLICABLE
    disposition: AxisValue = AxisMarker.NOT_APPLICABLE
    relation: AxisValue = AxisMarker.NOT_APPLICABLE
    provenance: AxisValue = AxisMarker.NOT_APPLICABLE

    def __post_init__(self) -> None:
        for item in fields(self):
            _axis(getattr(self, item.name), item.name)

    def bind(self, **changes: AxisValue) -> "ManaCoordinate":
        known = {item.name for item in fields(self)}
        unknown = set(changes) - known
        if unknown:
            raise ManaTensorError(f"unknown Mana axes: {sorted(unknown)}")
        return replace(self, **changes)

    def matches(self, **selectors: AxisValue) -> bool:
        known = {item.name for item in fields(self)}
        unknown = set(selectors) - known
        if unknown:
            raise ManaTensorError(f"unknown Mana axes: {sorted(unknown)}")
        return all(getattr(self, name) == value for name, value in selectors.items())

    def key(self) -> tuple[AxisValue, ...]:
        return tuple(getattr(self, item.name) for item in fields(self))


@dataclass(frozen=True)
class ManaTerm:
    coordinate: ManaCoordinate
    amount: int

    def __post_init__(self) -> None:
        _amount(self.amount)


@dataclass(frozen=True)
class ManaTensor:
    """Immutable sparse Mana state with one conserved total N.

    The tensor stores only current situated relations. Scalar quantities such as
    total Mana, local Ambient Mana, personal claims, or one Cast's Cost are
    projections/contractions over the same state rather than independent
    balances.
    """

    total_mana: int
    terms: tuple[ManaTerm, ...]

    def __post_init__(self) -> None:
        _amount(self.total_mana, "total_mana")
        normalized = self._normalize(self.terms)
        object.__setattr__(self, "terms", normalized)
        accounted = sum(term.amount for term in normalized)
        if accounted != self.total_mana:
            raise ManaTensorError(
                f"Mana conservation violated: tensor accounts for {accounted}, expected {self.total_mana}"
            )

    @classmethod
    def genesis(cls, total_mana: int, *, runtime: str, locality: str) -> "ManaTensor":
        coordinate = ManaCoordinate(
            runtime=runtime,
            locality=locality,
            disposition="ambient",
            relation="ambient",
        )
        return cls(total_mana, (ManaTerm(coordinate, total_mana),))

    @staticmethod
    def _normalize(terms: Iterable[ManaTerm]) -> tuple[ManaTerm, ...]:
        amounts: dict[ManaCoordinate, int] = {}
        for term in terms:
            if not isinstance(term, ManaTerm):
                raise ManaTensorError("Mana tensor terms must be ManaTerm values")
            amounts[term.coordinate] = amounts.get(term.coordinate, 0) + term.amount
        return tuple(
            ManaTerm(coordinate, amount)
            for coordinate, amount in sorted(amounts.items(), key=lambda item: item[0].key())
            if amount
        )

    def project(self, **selectors: AxisValue) -> tuple[ManaTerm, ...]:
        return tuple(term for term in self.terms if term.coordinate.matches(**selectors))

    def contract(self, **selectors: AxisValue) -> int:
        """Contract selected tensor axes to one scalar amount."""
        return sum(term.amount for term in self.project(**selectors))

    def cast_cost(self, cast_id: str) -> int:
        """Scalar contraction of Mana currently composed into one Cast."""
        if not isinstance(cast_id, str) or not cast_id:
            raise ManaTensorError("cast_id must be a non-empty string")
        return self.contract(cast=cast_id)

    def transition(
        self,
        source: ManaCoordinate,
        target: ManaCoordinate,
        amount: int,
    ) -> "ManaTensor":
        """Rebind Mana between exact coordinates while preserving N.

        Legal Magic operations decide whether a transition is admissible. This
        primitive only proves exact source availability and conservation.
        """
        _amount(amount)
        available = self.contract(**{
            item.name: getattr(source, item.name) for item in fields(source)
        })
        if available < amount:
            raise ManaTensorError(
                f"insufficient Mana at source coordinate: {available} < {amount}"
            )

        remaining = amount
        next_terms: list[ManaTerm] = []
        for term in self.terms:
            if term.coordinate == source and remaining:
                moved = min(term.amount, remaining)
                leftover = term.amount - moved
                if leftover:
                    next_terms.append(ManaTerm(term.coordinate, leftover))
                remaining -= moved
            else:
                next_terms.append(term)
        if remaining:
            raise ManaTensorError("source coordinate changed during transition")
        next_terms.append(ManaTerm(target, amount))
        return ManaTensor(self.total_mana, tuple(next_terms))

    def composition(self, **selectors: AxisValue) -> tuple[tuple[tuple[AxisValue, ...], int], ...]:
        """Canonical inspectable composition for evidence/tests/comparison."""
        return tuple((term.coordinate.key(), term.amount) for term in self.project(**selectors))
