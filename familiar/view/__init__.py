"""Familiar View: a bounded representation of one exact accepted revision.

A View is not the Familiar, not a Report, not Presence, and not runtime
authority. Its contract rests on `omission != absence`, which only holds if
every source guidance category is accounted for exactly once.
"""

from .builder import (
    SOURCE_CATEGORIES,
    FamiliarViewError,
    build_view,
    validate_view,
)

__all__ = [
    "SOURCE_CATEGORIES",
    "FamiliarViewError",
    "build_view",
    "validate_view",
]
