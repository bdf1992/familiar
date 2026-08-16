"""Semantic alignment evidence for autonomous Spellcraft.

Schema validation, AST restrictions, sandbox conformance, fuzzing and unit
tests can all pass while a generated implementation satisfies its tests through
behaviour that defeats the declared Effect. A synthesized Technique may be
structurally valid, capability-contained, and semantically pathological at the
same time. Structural safety is therefore not evidence of Effect alignment.

Four layers, and each answers a question the one before it cannot:

```text
structural validity   does it parse, type, and import within its constraints?
capability safety     can execution exceed the injected authority or scope?
behavioural evidence  what did it actually do across discriminating trials?
semantic effect       does it realize the declared Effect, on evidence
                      the candidate did not choose?
```

The last clause is the whole layer. A candidate that supplies its own trials is
supplying the answer along with the question, and tests written to a known
implementation stop discriminating between "realizes the Effect" and "satisfies
this suite".

**No candidate promotes itself.** Evidence whose provenance is the candidate is
recorded and never counted toward promotion.

**Fail closed.** Absent required semantic evidence, promotion is refused. Not
deferred, not provisional -- refused, because "we could not tell" and "it is
fine" are the two states this exists to keep apart.

Candidate mechanisms are open: independently generated adversarial cases,
metamorphic and property tests, differential comparison, counterexample search,
held-out trials, and explicit human acceptance. This module defines the
**evidence obligations**, not one evaluator.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Sequence

STRUCTURAL = "structural_validity"
CAPABILITY = "capability_safety"
BEHAVIOURAL = "behavioural_evidence"
SEMANTIC = "semantic_effect"

EVIDENCE_LAYERS = (STRUCTURAL, CAPABILITY, BEHAVIOURAL, SEMANTIC)

#: Where a piece of evidence came from. `candidate` never counts toward promotion.
CANDIDATE = "candidate"
INDEPENDENT = "independent"
HUMAN = "human"

PROMOTED = "promoted"
REFUSED = "refused"


class AlignmentError(ValueError):
    """An invariant, trial, or promotion request could not be expressed."""


@dataclass(frozen=True)
class EffectInvariant:
    """What realizing the Effect means, as something a trial can defeat.

    An invariant that no input can violate is not an invariant; it is a
    description. `check` receives the case and the observed result.
    """

    id: str
    description: str
    check: Callable[[Any, Any], bool]

    def __post_init__(self) -> None:
        for name in ("id", "description"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                raise AlignmentError(f"an Effect invariant requires {name}")
        if not callable(self.check):
            raise AlignmentError("an Effect invariant requires a callable check")


@dataclass(frozen=True)
class Trial:
    """A set of cases run against a candidate, and who chose them.

    `provenance` is the identity that selected the cases, not the identity that
    ran them. A held-out suite executed by the candidate's own harness is still
    independent; a suite the candidate wrote is not, however it is executed.
    """

    id: str
    provenance: str
    origin: str
    cases: Sequence[Any]

    def __post_init__(self) -> None:
        if self.origin not in (CANDIDATE, INDEPENDENT, HUMAN):
            raise AlignmentError(f"unknown trial origin: {self.origin}")
        if not isinstance(self.provenance, str) or not self.provenance:
            raise AlignmentError("a trial requires provenance")
        if self.origin != HUMAN and not list(self.cases):
            raise AlignmentError("a trial requires at least one case")

    @property
    def independent(self) -> bool:
        return self.origin in (INDEPENDENT, HUMAN)


@dataclass(frozen=True)
class TrialResult:
    trial_id: str
    provenance: str
    origin: str
    invariant_id: str
    passed: bool
    cases_run: int
    counterexamples: tuple[Any, ...] = ()
    detail: Mapping[str, Any] = field(default_factory=dict)

    @property
    def independent(self) -> bool:
        return self.origin in (INDEPENDENT, HUMAN)

    def as_dict(self) -> dict[str, Any]:
        return {
            "trial_id": self.trial_id,
            "provenance": self.provenance,
            "origin": self.origin,
            "invariant": self.invariant_id,
            "passed": self.passed,
            "cases_run": self.cases_run,
            "counterexamples": [repr(item) for item in self.counterexamples],
            "detail": dict(self.detail),
        }


def run_trial(
    implementation: Callable[[Any], Any],
    trial: Trial,
    invariant: EffectInvariant,
) -> TrialResult:
    """Run every case and keep the counterexamples rather than stopping at one.

    A single failing case is enough to refuse, but the whole set is what tells a
    reader whether the implementation is subtly wrong or wholly wrong.
    """
    counterexamples = []
    for case in trial.cases:
        try:
            result = implementation(case)
            held = bool(invariant.check(case, result))
        except Exception as exc:
            counterexamples.append(case)
            continue
        if not held:
            counterexamples.append(case)
    return TrialResult(
        trial_id=trial.id,
        provenance=trial.provenance,
        origin=trial.origin,
        invariant_id=invariant.id,
        passed=not counterexamples,
        cases_run=len(list(trial.cases)),
        counterexamples=tuple(counterexamples),
    )


@dataclass(frozen=True)
class HumanAcceptance:
    """Explicit acceptance by a named person, as one evidence source among others.

    Available at any stake, required only where policy says so. Requiring a
    human for every low-stake synthesis would make the layer unusable and is
    not what fail-closed means.
    """

    accepter: str
    invariant_id: str
    accepted: bool
    note: str = ""

    def as_result(self) -> TrialResult:
        return TrialResult(
            trial_id=f"human:{self.accepter}",
            provenance=self.accepter,
            origin=HUMAN,
            invariant_id=self.invariant_id,
            passed=self.accepted,
            cases_run=0,
            detail={"note": self.note},
        )


@dataclass(frozen=True)
class PromotionPolicy:
    """When a candidate may cross from candidate to trusted for this Environment."""

    #: Independent trial results required per invariant. Zero means the layer is
    #: not exercised, which `promote` refuses to treat as satisfied.
    independent_trials_required: int = 1
    require_human_acceptance: bool = False
    minimum_cases: int = 1


@dataclass(frozen=True)
class PromotionDecision:
    status: str
    reasons: tuple[str, ...]
    counted: tuple[TrialResult, ...] = ()
    recorded: tuple[TrialResult, ...] = ()

    @property
    def promoted(self) -> bool:
        return self.status == PROMOTED

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "reasons": list(self.reasons),
            "counted": [item.as_dict() for item in self.counted],
            "recorded": [item.as_dict() for item in self.recorded],
        }


def promote(
    invariant: EffectInvariant,
    results: Sequence[TrialResult],
    policy: PromotionPolicy,
    *,
    structural_ok: bool,
    capability_ok: bool,
) -> PromotionDecision:
    """Decide promotion, counting only evidence the candidate did not choose.

    Every result is retained in `recorded` -- including the candidate's own, and
    including failures -- because what was claimed is part of the account even
    when it does not count.
    """
    reasons: list[str] = []
    recorded = tuple(results)

    if not structural_ok:
        reasons.append(f"{STRUCTURAL}: not established")
    if not capability_ok:
        reasons.append(f"{CAPABILITY}: not established")

    for item in results:
        if item.invariant_id != invariant.id:
            raise AlignmentError(
                f"result {item.trial_id!r} tests {item.invariant_id!r}, not {invariant.id!r}"
            )

    counted = tuple(item for item in results if item.independent)
    self_supplied = [item for item in results if not item.independent]

    failing = [item for item in counted if not item.passed]
    if failing:
        reasons.append(
            f"{SEMANTIC}: invariant {invariant.id!r} defeated by "
            + ", ".join(item.trial_id for item in failing)
        )

    machine_counted = [item for item in counted if item.origin == INDEPENDENT]
    if len(machine_counted) < policy.independent_trials_required:
        reasons.append(
            f"{SEMANTIC}: {policy.independent_trials_required} independent trial(s) required, "
            f"{len(machine_counted)} present"
            + (f"; {len(self_supplied)} candidate-supplied result(s) do not count"
               if self_supplied else "")
        )

    thin = [item for item in machine_counted if item.cases_run < policy.minimum_cases]
    if thin:
        reasons.append(
            f"{BEHAVIOURAL}: trial(s) below the minimum of {policy.minimum_cases} case(s): "
            + ", ".join(item.trial_id for item in thin)
        )

    if policy.require_human_acceptance:
        accepted = [item for item in counted if item.origin == HUMAN and item.passed]
        if not accepted:
            reasons.append(f"{SEMANTIC}: policy requires explicit human acceptance")

    if reasons:
        return PromotionDecision(REFUSED, tuple(reasons), counted, recorded)
    return PromotionDecision(PROMOTED, (), counted, recorded)
