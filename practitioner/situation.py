from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CapabilityReceipt:
    name: str
    environment: str
    operations: tuple[str, ...]
    status: str
    authority: str
    locator: str
    evidence: str

    def supports(self, operation: str) -> bool:
        return self.status == "available" and operation in self.operations


@dataclass
class Situation:
    """Runtime view of the current cast, not portable Spell state."""

    id: str
    session_id: str
    caster: dict[str, Any]
    target: Any
    environments: tuple[str, ...] = ()
    capabilities: tuple[CapabilityReceipt, ...] = ()
    present_familiars: tuple[str, ...] = ()
    observations: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CastPlan:
    requirements: dict[str, CapabilityReceipt]
    gaps: tuple[str, ...]

    @property
    def ready(self) -> bool:
        return not self.gaps


def compile_cast_plan(requirements: dict[str, str], situation: Situation) -> CastPlan:
    """Bind requirement ids to concrete capability receipts by operation.

    This intentionally knows nothing about providers. OWL_ENGINE-compatible
    receipts can be projected into CapabilityReceipt and supplied here.
    """

    bindings: dict[str, CapabilityReceipt] = {}
    gaps: list[str] = []
    for requirement_id, operation in requirements.items():
        receipt = next((item for item in situation.capabilities if item.supports(operation)), None)
        if receipt is None:
            gaps.append(f"capability-missing:{requirement_id}:{operation}")
        else:
            bindings[requirement_id] = receipt
    return CastPlan(requirements=bindings, gaps=tuple(gaps))
