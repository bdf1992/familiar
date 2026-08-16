"""Ambient reactive reach beyond the directly injected capability.

Effect-path attenuation can correctly constrain what a Technique reaches
directly while the Environment still contains machinery outside that handle
hierarchy. A scoped file mutation may trigger watchers, CI, webhooks,
deployments, or subscriptions the Technique never invoked and could not have
invoked. Direct Scope enforcement is necessary and is not sufficient.

Four reaches, and the fourth is the one that is usually missing:

```text
direct     consequences the injected handle can invoke
declared   Environment mechanisms known to react to those mutations
observed   downstream effects independently attributable after execution
unknown    consequence space this Environment cannot prove absent
```

**A Cast must not claim a smaller blast radius because the Technique held a
narrow handle.** Attenuation bounds the first reach. It says nothing about the
second, and an Environment that cannot enumerate its own reactive machinery
must report `unknown` rather than an empty set.

Unknown is not a failure state. It is the honest one. Silently treating
unenumerated reach as absent is how a runtime comes to report a blast radius
of one file for a commit that triggered a deployment.

This does not weaken issue #10. The direct path must still be attenuated, and
this module observes rather than contains.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

DIRECT = "direct"
DECLARED = "declared"
OBSERVED = "observed"
UNKNOWN = "unknown"

REACHES = (DIRECT, DECLARED, OBSERVED, UNKNOWN)


class BlastRadiusError(ValueError):
    """A reactive declaration or observation could not be expressed."""


@dataclass(frozen=True)
class ReactiveEdge:
    """One Environment mechanism known to react to changes at a vertex."""

    source: str
    target: str
    mechanism: str

    def __post_init__(self) -> None:
        for name in ("source", "target", "mechanism"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                raise BlastRadiusError(f"a reactive edge requires {name}")

    def as_dict(self) -> dict[str, str]:
        return {"source": self.source, "target": self.target, "mechanism": self.mechanism}


class ReactiveGraph:
    """Declared reactive dependencies, and whether they are known to be complete.

    `complete=False` is the default because most Environments cannot prove they
    have enumerated every watcher. A graph that does not know it is complete
    produces an `unknown` reach alongside whatever it does declare.
    """

    def __init__(self, edges: Iterable[ReactiveEdge] = (), *, complete: bool = False):
        self._edges = tuple(edges)
        self.complete = bool(complete)

    @property
    def edges(self) -> tuple[ReactiveEdge, ...]:
        return self._edges

    def downstream(self, vertices: Iterable[str]) -> tuple[ReactiveEdge, ...]:
        """Transitively reachable edges from the directly mutated vertices."""
        frontier = list(dict.fromkeys(vertices))
        seen_vertices = set(frontier)
        reached: list[ReactiveEdge] = []
        while frontier:
            current = frontier.pop()
            for edge in self._edges:
                if edge.source != current or edge in reached:
                    continue
                reached.append(edge)
                if edge.target not in seen_vertices:
                    seen_vertices.add(edge.target)
                    frontier.append(edge.target)
        return tuple(reached)


@dataclass(frozen=True)
class DownstreamObservation:
    """An effect attributed after execution, independently of the Technique."""

    mechanism: str
    target: str
    observer: str
    detail: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("mechanism", "target", "observer"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                raise BlastRadiusError(f"a downstream observation requires {name}")

    def as_dict(self) -> dict[str, Any]:
        return {
            "mechanism": self.mechanism,
            "target": self.target,
            "observer": self.observer,
            "detail": dict(self.detail),
        }


@dataclass(frozen=True)
class BlastRadius:
    """What this Cast reached, and what it cannot say it did not reach."""

    direct: tuple[str, ...]
    declared: tuple[ReactiveEdge, ...]
    observed: tuple[DownstreamObservation, ...]
    unknown: bool
    unknown_reason: str | None = None

    @property
    def escaped_direct(self) -> tuple[DownstreamObservation, ...]:
        """Observed effects on targets outside the direct reach."""
        return tuple(item for item in self.observed if item.target not in self.direct)

    @property
    def contained(self) -> bool:
        """True only when nothing escaped AND nothing is unknown.

        Both conditions matter. An Environment that observed no escape but
        cannot enumerate its watchers has not established containment; it has
        established that it did not see anything.
        """
        return not self.escaped_direct and not self.unknown

    def as_dict(self) -> dict[str, Any]:
        return {
            "direct": list(self.direct),
            "declared": [item.as_dict() for item in self.declared],
            "observed": [item.as_dict() for item in self.observed],
            "unknown": self.unknown,
            "unknown_reason": self.unknown_reason,
            "escaped_direct": [item.as_dict() for item in self.escaped_direct],
            "contained": self.contained,
        }


def characterize(
    direct: Sequence[str],
    graph: ReactiveGraph | None,
    observations: Sequence[DownstreamObservation] = (),
) -> BlastRadius:
    """Describe reach without overstating what is known.

    No graph at all means the reactive space is entirely unenumerated, which is
    `unknown` with an empty declared set -- not a small blast radius.
    """
    if graph is None:
        return BlastRadius(
            direct=tuple(direct), declared=(), observed=tuple(observations),
            unknown=True, unknown_reason="no reactive dependency graph is available",
        )
    declared = graph.downstream(direct)
    if graph.complete:
        return BlastRadius(tuple(direct), declared, tuple(observations), unknown=False)
    return BlastRadius(
        direct=tuple(direct), declared=declared, observed=tuple(observations),
        unknown=True,
        unknown_reason="the reactive dependency graph is not known to be complete",
    )
