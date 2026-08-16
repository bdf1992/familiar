from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any

from .validation import validate_familiar


class FamiliarStoreError(ValueError):
    pass


class RevisionNotRetained(FamiliarStoreError):
    """The named revision was never retained by this store.

    Distinct from a stale, forged, or tampered reference. It means the bytes
    that revision named are absent because the store predates revision
    retention, not because the reference is wrong.
    """


STORE_FORMAT = "familiar-store/2"

_REVISION_FILE = re.compile(r"^r(\d{12})\.json$")


def _digest(value: dict[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + sha256(encoded).hexdigest()


def _id_key(familiar_id: str) -> str:
    return sha256(familiar_id.encode("utf-8")).hexdigest()


def _legacy_file_key(familiar_id: str) -> str:
    return _id_key(familiar_id) + ".json"


def _revision_file(revision: int) -> str:
    return f"r{revision:012d}.json"


def _atomic_json_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.parent.chmod(0o700)
    except OSError:
        pass
    fd, tmp_name = tempfile.mkstemp(prefix=".tmp-", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, sort_keys=True, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.chmod(tmp_name, 0o600)
        except OSError:
            pass
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


@dataclass(frozen=True)
class FamiliarRef:
    id: str
    caster_id: str
    revision: int
    digest: str


@dataclass(frozen=True)
class Retention:
    """What a store can still resolve for one Familiar identity.

    ``earliest_retained`` above 1 means earlier revisions were never retained
    by this store, which is a fact about the store's history and not a defect
    in any reference naming them.
    """

    id: str
    latest: int
    earliest_retained: int
    migrated_from_latest_only: bool


class FamiliarStore:
    """Exact caster-owned Familiar persistence. It grants no runtime authority.

    With no root path the store remains process-local for tests and ephemeral
    hosts. Supplying a root enables restart-safe local persistence. Directories
    and files use content-derived names so Familiar ids never become filesystem
    paths.

    Three concerns are kept apart:

    - immutable revision storage, keyed by Familiar identity and revision;
    - a latest pointer, which is a convenience index and never an authority;
    - exact resolution from a ``FamiliarRef``, which reads the named revision
      and never silently upgrades to latest.

    Writing revision N+1 never mutates or replaces the bytes an earlier valid
    ref names.
    """

    def __init__(self, root: str | Path | None = None):
        # id -> {revision -> familiar}
        self._values: dict[str, dict[int, dict[str, Any]]] = {}
        # id -> (latest, earliest_retained, migrated_from_latest_only)
        self._index: dict[str, tuple[int, int, bool]] = {}
        self.root = Path(root).expanduser().resolve() if root is not None else None
        if self.root is not None:
            self.root.mkdir(parents=True, exist_ok=True)
            try:
                self.root.chmod(0o700)
            except OSError:
                pass

    # -- paths -----------------------------------------------------------

    def _entry_dir(self, familiar_id: str) -> Path:
        if self.root is None:
            raise FamiliarStoreError("store has no persistent root")
        return self.root / _id_key(familiar_id)

    def _legacy_path(self, familiar_id: str) -> Path:
        if self.root is None:
            raise FamiliarStoreError("store has no persistent root")
        return self.root / _legacy_file_key(familiar_id)

    # -- envelopes -------------------------------------------------------

    @staticmethod
    def _open_envelope(envelope: Any, familiar_id: str, source: Path | None) -> tuple[int, dict[str, Any]]:
        where = f" at {source}" if source is not None else ""
        if not isinstance(envelope, dict):
            raise FamiliarStoreError(f"stored Familiar envelope is invalid{where}")
        if envelope.get("id") != familiar_id:
            raise FamiliarStoreError(f"stored Familiar id does not match lookup id{where}")
        revision = envelope.get("revision")
        value = envelope.get("familiar")
        if not isinstance(revision, int) or revision < 1 or not isinstance(value, dict):
            raise FamiliarStoreError(f"stored Familiar envelope is invalid{where}")
        validate_familiar(value)
        if envelope.get("digest") != _digest(value):
            raise FamiliarStoreError(f"stored Familiar digest does not match artifact{where}")
        return revision, value

    def _read_revision_file(self, familiar_id: str, revision: int) -> dict[str, Any] | None:
        path = self._entry_dir(familiar_id) / _revision_file(revision)
        if not path.exists():
            return None
        try:
            envelope = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise FamiliarStoreError(f"cannot read Familiar revision {revision}: {familiar_id}") from exc
        stored_revision, value = self._open_envelope(envelope, familiar_id, path)
        if stored_revision != revision:
            raise FamiliarStoreError(f"Familiar revision file {path.name} holds revision {stored_revision}")
        return value

    # -- index -----------------------------------------------------------

    def _scan_revisions(self, familiar_id: str) -> list[int]:
        entry = self._entry_dir(familiar_id)
        if not entry.is_dir():
            return []
        found = []
        for child in entry.iterdir():
            match = _REVISION_FILE.match(child.name)
            if match is not None and child.is_file():
                found.append(int(match.group(1)))
        return sorted(found)

    def _load_index(self, familiar_id: str) -> tuple[int, int, bool] | None:
        """Return (latest, earliest_retained, migrated) or None.

        The revision files are the truth. The manifest is a convenience index
        and is rebuilt from a directory scan whenever it is missing or
        disagrees with what is actually retained.
        """
        if self.root is None:
            return self._index.get(familiar_id)

        self._migrate_legacy_entry(familiar_id)
        revisions = self._scan_revisions(familiar_id)
        if not revisions:
            return None

        migrated = False
        manifest_path = self._entry_dir(familiar_id) / "manifest.json"
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise FamiliarStoreError(f"cannot read Familiar manifest: {familiar_id}") from exc
            if not isinstance(manifest, dict) or manifest.get("id") != familiar_id:
                raise FamiliarStoreError(f"Familiar manifest does not match lookup id: {familiar_id}")
            migrated = bool(manifest.get("migrated_from_latest_only", False))

        return revisions[-1], revisions[0], migrated

    def _write_manifest(self, familiar_id: str, latest: int, earliest: int, migrated: bool) -> None:
        _atomic_json_write(
            self._entry_dir(familiar_id) / "manifest.json",
            {
                "store_format": STORE_FORMAT,
                "id": familiar_id,
                "latest": latest,
                "earliest_retained": earliest,
                "migrated_from_latest_only": migrated,
            },
        )

    # -- migration -------------------------------------------------------

    def _migrate_legacy_entry(self, familiar_id: str) -> None:
        """Adopt a latest-only entry written by the previous store format.

        The legacy layout held exactly one envelope per Familiar id and
        overwrote it on every write, so revisions below the stored one were
        never retained. This adopts the stored revision as the only retained
        revision and records that fact. It does not invent revision history
        that never existed.
        """
        if self.root is None:
            return
        legacy = self._legacy_path(familiar_id)
        if not legacy.exists():
            return
        entry = self._entry_dir(familiar_id)
        if entry.is_dir() and self._scan_revisions(familiar_id):
            # Already migrated; the legacy file is stale residue.
            return
        try:
            envelope = json.loads(legacy.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise FamiliarStoreError(f"cannot read legacy Familiar entry: {familiar_id}") from exc
        revision, value = self._open_envelope(envelope, familiar_id, legacy)
        _atomic_json_write(
            entry / _revision_file(revision),
            {"id": familiar_id, "revision": revision, "digest": _digest(value), "familiar": value},
        )
        self._write_manifest(familiar_id, revision, revision, migrated=True)

    # -- public API ------------------------------------------------------

    def retention(self, familiar_id: str) -> Retention | None:
        """What this store can still resolve for one Familiar identity."""
        index = self._load_index(familiar_id)
        if index is None:
            return None
        latest, earliest, migrated = index
        return Retention(familiar_id, latest, earliest, migrated)

    def put(self, familiar: dict[str, Any], *, caster_id: str) -> FamiliarRef:
        validate_familiar(familiar)
        familiar_id = familiar["id"]
        if familiar["caster"]["id"] != caster_id:
            raise FamiliarStoreError("Familiar caster does not match committing caster")

        index = self._load_index(familiar_id)
        if index is None:
            revision, earliest, migrated = 1, 1, False
        else:
            latest, earliest, migrated = index
            revision = latest + 1

        value = deepcopy(familiar)
        digest = _digest(value)

        if self.root is None:
            revisions = self._values.setdefault(familiar_id, {})
            if revision in revisions:
                raise FamiliarStoreError(f"Familiar revision {revision} already exists: {familiar_id}")
            revisions[revision] = value
            self._index[familiar_id] = (revision, earliest, migrated)
        else:
            path = self._entry_dir(familiar_id) / _revision_file(revision)
            if path.exists():
                raise FamiliarStoreError(f"Familiar revision {revision} already exists: {familiar_id}")
            _atomic_json_write(
                path,
                {"id": familiar_id, "revision": revision, "digest": digest, "familiar": value},
            )
            self._write_manifest(familiar_id, revision, earliest, migrated)

        return FamiliarRef(familiar_id, caster_id, revision, digest)

    def resolve(self, ref: FamiliarRef) -> dict[str, Any]:
        """Resolve the exact revision the ref names. Never upgrades to latest."""
        index = self._load_index(ref.id)
        if index is None:
            raise FamiliarStoreError(f"Familiar not found: {ref.id}")
        latest, earliest, _migrated = index

        if self.root is None:
            value = self._values.get(ref.id, {}).get(ref.revision)
        else:
            value = self._read_revision_file(ref.id, ref.revision)

        if value is None:
            if 1 <= ref.revision < earliest:
                raise RevisionNotRetained(
                    f"Familiar revision {ref.revision} was never retained for {ref.id}; "
                    f"this store retains revisions {earliest} through {latest}"
                )
            raise FamiliarStoreError(f"Familiar revision not found: {ref.id} revision {ref.revision}")

        if _digest(value) != ref.digest:
            raise FamiliarStoreError("Familiar reference does not match stored artifact")
        if value["caster"]["id"] != ref.caster_id:
            raise FamiliarStoreError("Familiar ownership changed")
        return deepcopy(value)

    def resolve_latest(self, familiar_id: str) -> tuple[FamiliarRef, dict[str, Any]]:
        """Convenience access to the current revision.

        Returns the ref alongside the artifact so a caller that wanted an exact
        reference cannot mistake this for one it already held.
        """
        index = self._load_index(familiar_id)
        if index is None:
            raise FamiliarStoreError(f"Familiar not found: {familiar_id}")
        latest, _earliest, _migrated = index
        if self.root is None:
            value = self._values.get(familiar_id, {}).get(latest)
        else:
            value = self._read_revision_file(familiar_id, latest)
        if value is None:
            raise FamiliarStoreError(f"Familiar revision not found: {familiar_id} revision {latest}")
        ref = FamiliarRef(familiar_id, value["caster"]["id"], latest, _digest(value))
        return ref, deepcopy(value)
