from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ID_PATTERN = r"^[a-z0-9][a-z0-9_.-]*$"
SPELL_NAME_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
SEMVER_PATTERN = r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?$"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class Telemetry(StrictModel):
    id: str = Field(pattern=ID_PATTERN)
    description: str = Field(min_length=1)
    max_age_ms: int | None = Field(default=None, ge=0)


class SchemaDeclaration(StrictModel):
    id: str = Field(pattern=ID_PATTERN)
    description: str = Field(min_length=1)
    ref: str | None = Field(default=None, min_length=1)
    schema_: dict[str, Any] | None = Field(default=None, alias="schema")

    @model_validator(mode="after")
    def exactly_one_source(self) -> "SchemaDeclaration":
        if (self.ref is None) == (self.schema_ is None):
            raise ValueError("schema declaration requires exactly one of ref or schema")
        return self


class ProtocolContract(StrictModel):
    id: str = Field(pattern=ID_PATTERN)
    ref: str = Field(min_length=1)
    version: str = Field(min_length=1)
    roles: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_roles(self) -> "ProtocolContract":
        if len(self.roles) != len(set(self.roles)):
            raise ValueError("protocol roles must be unique")
        return self


class RuntimeContract(StrictModel):
    protocols: list[str] = Field(default_factory=list)


class BindingSelector(StrictModel):
    operation: str = Field(min_length=1)
    capability: str | None = Field(default=None, min_length=1)
    protocol: str | None = Field(default=None, pattern=ID_PATTERN)
    environment: str | None = Field(default=None, min_length=1)
    subject: str | None = Field(default=None, min_length=1)
    authority: str | None = Field(default=None, min_length=1)
    locator: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def concrete_identity(self) -> "BindingSelector":
        if not any((self.capability, self.protocol, self.locator)):
            raise ValueError(
                "binding selector must identify at least one capability, protocol, or locator"
            )
        return self


class InterfaceSlot(StrictModel):
    schema_: str = Field(alias="schema", pattern=ID_PATTERN)
    description: str | None = Field(default=None, min_length=1)


class EffectInterface(StrictModel):
    input: InterfaceSlot | None = None
    target: InterfaceSlot | None = None
    result: InterfaceSlot | None = None


class ScopeConstraint(StrictModel):
    max_items: int = Field(ge=0)
    enforcement: Literal["effect_path"]


class CostConstraint(StrictModel):
    resource: str = Field(min_length=1)
    max: int = Field(ge=0)


class DurationConstraint(StrictModel):
    execution_max_ms: int = Field(ge=1)


class CheckRequirement(StrictModel):
    id: str = Field(pattern=ID_PATTERN)
    description: str = Field(min_length=1)
    check: str = Field(min_length=1)
    binding: BindingSelector


class AuthorityRequirement(StrictModel):
    id: str = Field(pattern=ID_PATTERN)
    description: str | None = Field(default=None, min_length=1)
    authority: str = Field(min_length=1)
    binding: BindingSelector


class ScopeRequirement(StrictModel):
    id: str = Field(pattern=ID_PATTERN)
    description: str | None = Field(default=None, min_length=1)
    scope: ScopeConstraint
    binding: BindingSelector


class CostRequirement(StrictModel):
    id: str = Field(pattern=ID_PATTERN)
    description: str | None = Field(default=None, min_length=1)
    cost: CostConstraint
    binding: BindingSelector


class DurationRequirement(StrictModel):
    id: str = Field(pattern=ID_PATTERN)
    description: str | None = Field(default=None, min_length=1)
    duration: DurationConstraint
    binding: BindingSelector


BeforeRequirement = CheckRequirement | AuthorityRequirement | ScopeRequirement
DuringRequirement = CostRequirement | DurationRequirement
AfterRequirement = CheckRequirement


class Requirements(StrictModel):
    before: list[BeforeRequirement] = Field(default_factory=list)
    during: list[DuringRequirement] = Field(default_factory=list)
    after: list[AfterRequirement] = Field(default_factory=list)


class Effect(StrictModel):
    id: str = Field(pattern=ID_PATTERN)
    description: str = Field(min_length=1)
    telemetry: list[str] = Field(default_factory=list)
    interface: EffectInterface | None = None
    requirements: Requirements

    @model_validator(mode="after")
    def unique_telemetry(self) -> "Effect":
        if len(self.telemetry) != len(set(self.telemetry)):
            raise ValueError("effect telemetry references must be unique")
        return self


class ImplementationSuggestion(StrictModel):
    id: str = Field(pattern=ID_PATTERN)
    kind: Literal["skill", "mcp", "script", "service", "host", "package"]
    locator: str = Field(min_length=1)
    effects: list[str] = Field(min_length=1)
    protocols: list[str] = Field(default_factory=list)
    binding: str | None = Field(default=None, min_length=1)
    description: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def unique_refs(self) -> "ImplementationSuggestion":
        if len(self.effects) != len(set(self.effects)):
            raise ValueError("implementation effect references must be unique")
        if len(self.protocols) != len(set(self.protocols)):
            raise ValueError("implementation protocol references must be unique")
        return self


class SpellDeclaration(StrictModel):
    spell_format: Literal["0.3"]
    name: str = Field(min_length=1, max_length=64, pattern=SPELL_NAME_PATTERN)
    version: str = Field(pattern=SEMVER_PATTERN)
    description: str = Field(min_length=1, max_length=1024)
    schemas: list[SchemaDeclaration] = Field(default_factory=list)
    protocols: list[ProtocolContract] = Field(default_factory=list)
    runtime: RuntimeContract = Field(default_factory=RuntimeContract)
    telemetry: list[Telemetry] = Field(default_factory=list)
    implementations: list[ImplementationSuggestion] = Field(default_factory=list)
    effects: list[Effect] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_references(self) -> "SpellDeclaration":
        schema_ids = [item.id for item in self.schemas]
        protocol_ids = [item.id for item in self.protocols]
        telemetry_ids = [item.id for item in self.telemetry]
        effect_ids = [item.id for item in self.effects]

        self._require_unique("schema", schema_ids)
        self._require_unique("protocol", protocol_ids)
        self._require_unique("telemetry", telemetry_ids)
        self._require_unique("effect", effect_ids)

        schema_set = set(schema_ids)
        protocol_set = set(protocol_ids)
        telemetry_set = set(telemetry_ids)
        effect_set = set(effect_ids)

        missing_runtime_protocols = set(self.runtime.protocols) - protocol_set
        if missing_runtime_protocols:
            raise ValueError(
                f"runtime protocol references do not resolve: {sorted(missing_runtime_protocols)}"
            )

        for effect in self.effects:
            missing_telemetry = set(effect.telemetry) - telemetry_set
            if missing_telemetry:
                raise ValueError(
                    f"effect {effect.id} telemetry references do not resolve: "
                    f"{sorted(missing_telemetry)}"
                )
            if effect.interface:
                for slot_name in ("input", "target", "result"):
                    slot = getattr(effect.interface, slot_name)
                    if slot and slot.schema_ not in schema_set:
                        raise ValueError(
                            f"effect {effect.id} {slot_name} schema does not resolve: {slot.schema_}"
                        )

            all_requirements = [
                *effect.requirements.before,
                *effect.requirements.during,
                *effect.requirements.after,
            ]
            requirement_ids = [item.id for item in all_requirements]
            self._require_unique(f"requirement in effect {effect.id}", requirement_ids)

            scopes = [item for item in effect.requirements.before if isinstance(item, ScopeRequirement)]
            if len(scopes) > 1:
                raise ValueError(f"effect {effect.id} may declare at most one scope requirement")

            durations = [
                item for item in effect.requirements.during
                if isinstance(item, DurationRequirement)
            ]
            if len(durations) > 1:
                raise ValueError(
                    f"effect {effect.id} may declare at most one execution duration requirement"
                )

            cost_resources = [
                item.cost.resource for item in effect.requirements.during
                if isinstance(item, CostRequirement)
            ]
            self._require_unique(f"cost resource in effect {effect.id}", cost_resources)

            for requirement in all_requirements:
                if requirement.binding.protocol and requirement.binding.protocol not in protocol_set:
                    raise ValueError(
                        f"requirement {effect.id}.{requirement.id} protocol does not resolve: "
                        f"{requirement.binding.protocol}"
                    )

        for implementation in self.implementations:
            missing_effects = set(implementation.effects) - effect_set
            if missing_effects:
                raise ValueError(
                    f"implementation {implementation.id} effect references do not resolve: "
                    f"{sorted(missing_effects)}"
                )
            missing_protocols = set(implementation.protocols) - protocol_set
            if missing_protocols:
                raise ValueError(
                    f"implementation {implementation.id} protocol references do not resolve: "
                    f"{sorted(missing_protocols)}"
                )

        return self

    @staticmethod
    def _require_unique(label: str, values: list[str]) -> None:
        if len(values) != len(set(values)):
            raise ValueError(f"{label} ids/values must be unique")


def json_schema() -> dict[str, Any]:
    schema = SpellDeclaration.model_json_schema(by_alias=True)
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "https://agentspells.dev/schema/spell-frontmatter-0.3-draft.json"
    schema["title"] = "Agent Spells SPELL.md 0.3 draft frontmatter"
    return schema


def write_json_schema(path: str | Path) -> None:
    target = Path(path)
    target.write_text(
        __import__("json").dumps(json_schema(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
