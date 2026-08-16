"""Environment-owned effect-path boundaries for Scope enforcement.

A Scope Requirement is enforced only when the effectful execution path is
bounded to the exact scope resolved before closure. Resolving which targets are
admissible is one thing; making the forbidden consequence impossible or
observable is another, and only the Environment can do the second. A Technique
Binding claiming `scope: [max_items]` is metadata until a concrete mechanism
stands behind it.

The Kernel specifies the contract and calls whatever boundary it is handed. It
does not construct one, because a runtime that supplies its own containment is
attesting to its own honesty. This module carries one reference mechanism -- a
filtered object capability over a mapping target. An attenuated filesystem
view, a scoped API token, or a sandbox namespace conform equally by satisfying
the same contract.
"""

from __future__ import annotations

from collections.abc import MutableMapping
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Iterator


class ScopeViolationError(RuntimeError):
    """A Technique reached outside the resolved Scope through its handle."""


@dataclass(frozen=True)
class ScopeViolation:
    operation: str
    key: Any

    def as_dict(self) -> dict[str, Any]:
        return {"operation": self.operation, "key": str(self.key)}


class ScopeBoundary:
    """The contract the Kernel requires of any Scope enforcement mechanism.

    `handle()` is what the Technique executes through. `violations()` is what
    the Kernel reads afterwards, so an attempt that the Technique caught and
    swallowed is still attributable rather than silently absent.
    """

    mechanism: str = "unnamed"

    def handle(self) -> Any:  # pragma: no cover - interface
        raise NotImplementedError

    def violations(self) -> tuple[ScopeViolation, ...]:  # pragma: no cover - interface
        raise NotImplementedError

    def describe(self) -> dict[str, Any]:  # pragma: no cover - interface
        raise NotImplementedError


class _ScopedMapping(MutableMapping):
    """A mapping view exposing only the admissible keys of its source.

    Reaching a key outside the admissible set raises and is recorded. Both
    matter: raising makes the mutation impossible, recording makes the attempt
    observable even when the Technique swallows the exception.
    """

    def __init__(self, source: MutableMapping, admissible: frozenset, violations: list[ScopeViolation]):
        self._source = source
        self._admissible = admissible
        self._violations = violations

    def _guard(self, operation: str, key: Any) -> None:
        if key not in self._admissible:
            self._violations.append(ScopeViolation(operation, key))
            raise ScopeViolationError(f"{operation} outside resolved Scope: {key!r}")

    def __getitem__(self, key: Any) -> Any:
        self._guard("read", key)
        return self._source[key]

    def __setitem__(self, key: Any, value: Any) -> None:
        self._guard("write", key)
        self._source[key] = value

    def __delitem__(self, key: Any) -> None:
        self._guard("delete", key)
        del self._source[key]

    def __iter__(self) -> Iterator:
        return iter(key for key in self._source if key in self._admissible)

    def __len__(self) -> int:
        return sum(1 for key in self._source if key in self._admissible)

    def __repr__(self) -> str:
        return f"_ScopedMapping({sorted(map(str, self._admissible))})"


class MappingScopeBoundary(ScopeBoundary):
    """Filtered object capability over a mapping target."""

    mechanism = "environment.mapping-view"

    def __init__(self, target: MutableMapping, admissible: Iterable[Any]):
        if not isinstance(target, MutableMapping):
            raise TypeError("MappingScopeBoundary requires a mutable mapping target")
        self._target = target
        self._admissible = frozenset(admissible)
        self._violations: list[ScopeViolation] = []

    def handle(self) -> _ScopedMapping:
        return _ScopedMapping(self._target, self._admissible, self._violations)

    def violations(self) -> tuple[ScopeViolation, ...]:
        return tuple(self._violations)

    def describe(self) -> dict[str, Any]:
        return {
            "mechanism": self.mechanism,
            "admissible": sorted(str(key) for key in self._admissible),
        }


ScopeEnforcer = Callable[[Any, list, dict], ScopeBoundary]


def mapping_scope_enforcer(admissible: Iterable[Any]) -> ScopeEnforcer:
    """Bound the effect path to a fixed admissible key set on a mapping target.

    The admissible set is the Environment's declaration of what this Cast may
    reach. It is not read from the Technique Binding, because a claim by the
    thing being contained is not containment.
    """
    frozen = frozenset(admissible)

    def enforce(target: Any, resolved_items: list, context: dict) -> ScopeBoundary:
        return MappingScopeBoundary(target, frozen)

    return enforce
