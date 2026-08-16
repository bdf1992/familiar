"""Environment-owned attenuated credentials for Authority enforcement.

Authority resolution answers whether the caster may attempt the declared effect
against the resolved target. It does not constrain what the executor can
actually reach. A Technique running with ambient host credentials is bounded by
those credentials, not by the resolver that returned true.

This is the same defect Scope had, at a different boundary, and it takes the
same shape of fix: the Kernel specifies a contract and calls whatever boundary
it is handed, and the Environment supplies the concrete credential. This module
carries one reference mechanism -- a credential attenuated to the exact
permissions that were resolved. A scoped API token, an assumed role with a
narrowed policy, or a per-cast service identity conform equally.

`environment/scope.py` carries the parallel boundary for Scope.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable


class AuthorityViolationError(RuntimeError):
    """A Technique attempted an action beyond the authority that closed the Cast."""


@dataclass(frozen=True)
class AuthorityViolation:
    permission: str
    resource: str | None

    def as_dict(self) -> dict[str, Any]:
        return {"permission": self.permission, "resource": self.resource}


class AuthorityBoundary:
    """The contract the Kernel requires of any Authority enforcement mechanism.

    `handle()` is the credential the Technique executes through. `violations()`
    is what the Kernel reads afterwards, so an attempt the Technique caught is
    still attributable.
    """

    mechanism: str = "unnamed"

    def handle(self) -> Any:  # pragma: no cover - interface
        raise NotImplementedError

    def violations(self) -> tuple[AuthorityViolation, ...]:  # pragma: no cover - interface
        raise NotImplementedError

    def describe(self) -> dict[str, Any]:  # pragma: no cover - interface
        raise NotImplementedError


class _AttenuatedCredential:
    """A credential permitting only the resolved permissions and resources.

    It holds the broader host credential privately. A Technique given this
    object cannot widen it back, because the only way through is `act()`.
    """

    def __init__(
        self,
        host_credential: Any,
        granted: frozenset,
        resources: frozenset | None,
        violations: list[AuthorityViolation],
    ):
        self._host_credential = host_credential
        self._granted = granted
        self._resources = resources
        self._violations = violations

    @property
    def granted(self) -> tuple[str, ...]:
        return tuple(sorted(self._granted))

    def act(self, permission: str, resource: str | None = None, **kwargs: Any) -> Any:
        if permission not in self._granted:
            self._violations.append(AuthorityViolation(permission, resource))
            raise AuthorityViolationError(f"permission beyond resolved authority: {permission!r}")
        if self._resources is not None and resource not in self._resources:
            self._violations.append(AuthorityViolation(permission, resource))
            raise AuthorityViolationError(f"resource beyond resolved authority: {resource!r}")
        return self._host_credential.act(permission, resource, **kwargs)

    def __repr__(self) -> str:
        return f"_AttenuatedCredential(granted={self.granted})"


class AttenuatedCredentialBoundary(AuthorityBoundary):
    """Narrow a host credential to exactly the authority that closed the Cast."""

    mechanism = "environment.attenuated-credential"

    def __init__(
        self,
        host_credential: Any,
        granted: Iterable[str],
        *,
        resources: Iterable[str] | None = None,
    ):
        if not hasattr(host_credential, "act"):
            raise TypeError("host credential must expose act(permission, resource, **kwargs)")
        self._host_credential = host_credential
        self._granted = frozenset(granted)
        self._resources = frozenset(resources) if resources is not None else None
        self._violations: list[AuthorityViolation] = []

    def handle(self) -> _AttenuatedCredential:
        return _AttenuatedCredential(
            self._host_credential, self._granted, self._resources, self._violations
        )

    def violations(self) -> tuple[AuthorityViolation, ...]:
        return tuple(self._violations)

    def describe(self) -> dict[str, Any]:
        described = {
            "mechanism": self.mechanism,
            "granted": sorted(self._granted),
        }
        if self._resources is not None:
            described["resources"] = sorted(self._resources)
        return described


class RecordingHostCredential:
    """A reference host credential that records what was permitted through it.

    Real hosts wrap a token, a role, or a service identity. This one performs
    no side effect, which makes it the right stand-in wherever an Effect needs
    an attenuated credential to exist without the Technique acting through it
    for real. What it records is the acts that passed attenuation, so a test
    can assert what actually got through rather than what was requested.
    """

    def __init__(self):
        self.acts: list[tuple[str, str | None]] = []

    def act(self, permission: str, resource: str | None = None, **kwargs: Any) -> dict[str, Any]:
        self.acts.append((permission, resource))
        return {"permission": permission, "resource": resource, **kwargs}


AuthorityEnforcer = Callable[[dict, list, dict], AuthorityBoundary]


def attenuated_credential_enforcer(
    host_credential: Any,
    *,
    resources: Iterable[str] | None = None,
) -> AuthorityEnforcer:
    """Attenuate a host credential to the authorities the Kernel resolved.

    The granted set comes from the Kernel's resolution, not from the Technique
    Binding. A Technique declaring `authority: true` is claiming participation,
    never granting itself the credential.
    """

    def enforce(caster: dict, granted: list, context: dict) -> AuthorityBoundary:
        return AttenuatedCredentialBoundary(host_credential, granted, resources=resources)

    return enforce
