"""Small, skill-format-neutral kernel for skill collections and builds.

The kernel deliberately knows nothing about how an artifact is installed or
executed.  Adapters own those boundaries.  This module only validates a
collection graph, accounts for skill points, and emits immutable unlock
receipts.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from types import MappingProxyType
from typing import Any, Iterable, Mapping


class SkillTreeError(ValueError):
    """The collection or requested build transition is invalid."""


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SkillTreeError(f"{field} must be non-empty text")
    return value.strip()


def _text_tuple(value: Any, field: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise SkillTreeError(f"{field} must be a list")
    result = tuple(_text(item, field) for item in value)
    if len(result) != len(set(result)):
        raise SkillTreeError(f"{field} must not contain duplicates")
    return result


@dataclass(frozen=True)
class ArtifactRef:
    """An adapter-owned reference to an executable or instructive artifact."""

    adapter: str
    locator: str
    digest: str | None = None

    @classmethod
    def from_mapping(cls, value: Any) -> "ArtifactRef":
        if not isinstance(value, dict):
            raise SkillTreeError("artifact must be an object")
        digest = value.get("digest")
        if digest is not None:
            digest = _text(digest, "artifact.digest")
        return cls(
            adapter=_text(value.get("adapter"), "artifact.adapter"),
            locator=_text(value.get("locator"), "artifact.locator"),
            digest=digest,
        )


@dataclass(frozen=True)
class SkillNode:
    """One selectable skill and its graph relations."""

    id: str
    title: str
    point_cost: int
    requires: tuple[str, ...]
    artifact: ArtifactRef
    lesson_refs: tuple[str, ...] = ()

    @classmethod
    def from_mapping(cls, value: Any) -> "SkillNode":
        if not isinstance(value, dict):
            raise SkillTreeError("each skill must be an object")
        point_cost = value.get("point_cost")
        if isinstance(point_cost, bool) or not isinstance(point_cost, int) or point_cost < 0:
            raise SkillTreeError("point_cost must be a non-negative integer")
        return cls(
            id=_text(value.get("id"), "skill.id"),
            title=_text(value.get("title"), "skill.title"),
            point_cost=point_cost,
            requires=_text_tuple(value.get("requires", []), "skill.requires"),
            artifact=ArtifactRef.from_mapping(value.get("artifact")),
            lesson_refs=_text_tuple(value.get("lesson_refs", []), "skill.lesson_refs"),
        )


@dataclass(frozen=True)
class Build:
    """A participant's selected skills under one exact collection revision."""

    collection_id: str
    collection_version: str
    collection_revision: str
    skill_points: int
    unlocked: tuple[str, ...] = ()


@dataclass(frozen=True)
class UnlockReceipt:
    """The attributable result of one build transition."""

    skill_id: str
    before: Build
    after: Build
    points_spent: int


class Collection:
    """A validated skill graph from which tree and build views are projected."""

    def __init__(self, collection_id: str, version: str, skills: Iterable[SkillNode]):
        self.id = _text(collection_id, "collection_id")
        self.version = _text(version, "version")
        nodes: dict[str, SkillNode] = {}
        for node in skills:
            if node.id in nodes:
                raise SkillTreeError(f"duplicate skill id: {node.id}")
            nodes[node.id] = node
        if not nodes:
            raise SkillTreeError("a collection must contain at least one skill")
        self._skills: Mapping[str, SkillNode] = MappingProxyType(nodes)
        self._validate_relations()
        material = [
            {
                "id": node.id,
                "title": node.title,
                "point_cost": node.point_cost,
                "requires": list(node.requires),
                "artifact": {
                    "adapter": node.artifact.adapter,
                    "locator": node.artifact.locator,
                    "digest": node.artifact.digest,
                },
                "lesson_refs": list(node.lesson_refs),
            }
            for node in sorted(nodes.values(), key=lambda item: item.id)
        ]
        encoded = json.dumps(
            {"collection_id": self.id, "version": self.version, "skills": material},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        self.revision = f"sha256:{hashlib.sha256(encoded).hexdigest()}"
    @classmethod
    def from_mapping(cls, value: Any) -> "Collection":
        if not isinstance(value, dict):
            raise SkillTreeError("collection must be an object")
        raw_skills = value.get("skills")
        if not isinstance(raw_skills, list):
            raise SkillTreeError("skills must be a list")
        return cls(
            collection_id=_text(value.get("collection_id"), "collection_id"),
            version=_text(value.get("version"), "version"),
            skills=(SkillNode.from_mapping(item) for item in raw_skills),
        )

    @property
    def skills(self) -> Mapping[str, SkillNode]:
        return self._skills

    def new_build(self, skill_points: int) -> Build:
        if isinstance(skill_points, bool) or not isinstance(skill_points, int) or skill_points < 0:
            raise SkillTreeError("skill_points must be a non-negative integer")
        return Build(self.id, self.version, self.revision, skill_points)

    def spent_points(self, build: Build) -> int:
        self._validate_build(build)
        return sum(self._skills[skill_id].point_cost for skill_id in build.unlocked)

    def unlock(self, build: Build, skill_id: str) -> UnlockReceipt:
        """Unlock one skill or refuse without changing the supplied build."""

        self._validate_build(build)
        skill_id = _text(skill_id, "skill_id")
        if skill_id not in self._skills:
            raise SkillTreeError(f"unknown skill: {skill_id}")
        if skill_id in build.unlocked:
            raise SkillTreeError(f"skill already unlocked: {skill_id}")
        node = self._skills[skill_id]
        missing = tuple(required for required in node.requires if required not in build.unlocked)
        if missing:
            raise SkillTreeError(f"missing prerequisites for {skill_id}: {', '.join(missing)}")
        if self.spent_points(build) + node.point_cost > build.skill_points:
            raise SkillTreeError(f"insufficient skill points for {skill_id}")
        after = Build(
            collection_id=build.collection_id,
            collection_version=build.collection_version,
            collection_revision=build.collection_revision,
            skill_points=build.skill_points,
            unlocked=build.unlocked + (skill_id,),
        )
        return UnlockReceipt(skill_id, build, after, node.point_cost)

    def project_tree(self) -> tuple[dict[str, Any], ...]:
        """Return a non-authoritative tree view of the canonical graph.

        A node with multiple prerequisites can appear beneath multiple parents.
        Its stable id preserves identity across those repeated projections.
        """

        dependents = {skill_id: [] for skill_id in self._skills}
        for node in self._skills.values():
            for required in node.requires:
                dependents[required].append(node.id)
        for children in dependents.values():
            children.sort()

        def branch(skill_id: str, ancestry: frozenset[str]) -> dict[str, Any]:
            if skill_id in ancestry:
                raise SkillTreeError(f"cycle encountered while projecting: {skill_id}")
            node = self._skills[skill_id]
            return {
                "id": node.id,
                "title": node.title,
                "point_cost": node.point_cost,
                "children": tuple(
                    branch(child, ancestry | {skill_id}) for child in dependents[skill_id]
                ),
            }

        roots = sorted(node.id for node in self._skills.values() if not node.requires)
        return tuple(branch(root, frozenset()) for root in roots)

    def _validate_relations(self) -> None:
        for node in self._skills.values():
            if node.id in node.requires:
                raise SkillTreeError(f"skill cannot require itself: {node.id}")
            missing = tuple(required for required in node.requires if required not in self._skills)
            if missing:
                raise SkillTreeError(f"unknown prerequisites for {node.id}: {', '.join(missing)}")

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(skill_id: str) -> None:
            if skill_id in visiting:
                raise SkillTreeError(f"prerequisite cycle includes: {skill_id}")
            if skill_id in visited:
                return
            visiting.add(skill_id)
            for required in self._skills[skill_id].requires:
                visit(required)
            visiting.remove(skill_id)
            visited.add(skill_id)

        for skill_id in self._skills:
            visit(skill_id)

    def _validate_build(self, build: Build) -> None:
        if (
            build.collection_id != self.id
            or build.collection_version != self.version
            or build.collection_revision != self.revision
        ):
            raise SkillTreeError("build belongs to a different collection revision")
        if isinstance(build.skill_points, bool) or not isinstance(build.skill_points, int):
            raise SkillTreeError("build skill_points must be an integer")
        if build.skill_points < 0 or len(build.unlocked) != len(set(build.unlocked)):
            raise SkillTreeError("build state is invalid")
        seen: set[str] = set()
        for skill_id in build.unlocked:
            if skill_id not in self._skills:
                raise SkillTreeError(f"build contains unknown skill: {skill_id}")
            missing = tuple(required for required in self._skills[skill_id].requires if required not in seen)
            if missing:
                raise SkillTreeError(
                    f"build unlock order omits prerequisites for {skill_id}: {', '.join(missing)}"
                )
            seen.add(skill_id)
        if sum(self._skills[skill_id].point_cost for skill_id in seen) > build.skill_points:
            raise SkillTreeError("build spends more skill points than it owns")
