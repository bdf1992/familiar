"""Work surface for resolving a read-only Domain Handle.

This package is intentionally not a Current protocol interface. Issue #67 owns
its standing. Context, Domain Familiarity, and Subject Familiar remain distinct
inputs; resolving them creates a representation, not runtime authority.
"""

from .resolver import DomainHandleError, resolve_domain_handle

__all__ = ["DomainHandleError", "resolve_domain_handle"]
