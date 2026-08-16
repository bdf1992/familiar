"""Canonical resolution of cross-domain resources.

Runtime code reaches another domain's artifacts by that domain's canonical
repository path. It does not reach them through composition symlinks such as
the former ``cast/format``, ``cast/familiar`` and ``cast/owl``.

Those symlinks do not materialise as links on a checkout without symlink
support -- Windows without Developer Mode, or any checkout with
``core.symlinks=false`` -- where Git writes an ordinary file containing the
target path instead. Every schema load through such a path then fails, so
runtime dependence on them makes the supported test command platform
dependent. Navigation aids may be reintroduced; executable correctness may not
depend on them.
"""

from __future__ import annotations

from pathlib import Path

# cast/kernel/resources.py -> cast/kernel -> cast -> repository root
REPO_ROOT = Path(__file__).resolve().parents[2]

#: The five owned domains. A canonical resource path begins with one of them.
DOMAINS = ("spell", "cast", "familiar", "registry", "environment")

SPELL_DOMAIN = REPO_ROOT / "spell"
CAST_DOMAIN = REPO_ROOT / "cast"
FAMILIAR_DOMAIN = REPO_ROOT / "familiar"
REGISTRY_DOMAIN = REPO_ROOT / "registry"
ENVIRONMENT_DOMAIN = REPO_ROOT / "environment"


class ResourceError(RuntimeError):
    """A canonical resource could not be resolved."""


def resource(*parts: str) -> Path:
    """Resolve a repository-root-relative resource path.

    Raises ``ResourceError`` naming the resolved path when it does not exist,
    rather than letting a reader fail later with a message about JSON.
    """
    if not parts:
        raise ResourceError("no resource path given")
    if parts[0] not in DOMAINS:
        raise ResourceError(
            f"{parts[0]!r} is not an owned domain; expected one of {', '.join(DOMAINS)}"
        )
    path = REPO_ROOT.joinpath(*parts)
    if not path.exists():
        raise ResourceError(f"canonical resource not found: {path}")
    return path


SPELL_SCHEMA = REPO_ROOT / "spell" / "format" / "spell.schema.json"
SPELL_FORMAT_SPEC = REPO_ROOT / "spell" / "format" / "SPECIFICATION.md"
FAMILIAR_SCHEMA = REPO_ROOT / "familiar" / "familiar.schema.json"
FAMILIAR_VIEW_SCHEMA = REPO_ROOT / "familiar" / "view" / "familiar-view.schema.json"
OWL_PATH = REPO_ROOT / "familiar" / "owl" / "owl.json"
CAST_SCHEMA = REPO_ROOT / "cast" / "kernel" / "cast.schema.json"
