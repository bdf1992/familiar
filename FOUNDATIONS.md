# Foundations

This file anchors the distinctions Familiar and its retained Agent Spells
profile must preserve. It explains meaning; it does not silently create runtime
requirements, new `SPELL.md` fields, or a universal skill format.

## Core distinctions

- **Spell is not Cast.** A Spell declares a possible Effect and the Requirements under which it may count. A Cast is one situated attempt under the casting law.
- **Pointing is not casting.** A practitioner may point at the known, toward the partially known, or into the unknown. Pointing establishes a distinction or direction of attention; it does not imply target resolution, authority, closure, or execution.
- **Knowledge is not consequence.** Scrolls, Spellbooks, Libraries, publication, subscription, registration, and resolution may change knowledge or addressability. Only casting may attempt an Effect.
- **Identity is not Presence.** An existing thing may become present in a context without being created there. Releasing Presence does not destroy the underlying thing.
- **Meaning is not expression.** Different Familiars, representations, or Techniques may vary while the load-bearing meaning of a Spell remains unchanged.
- **Effect is not Technique.** A Technique is one implementation path used to attempt an Effect. Replacing a Technique should not require redefining the Spell when the Effect contract is unchanged.
- **Requirement is not assertion.** A Requirement is governable only when the current Situation exposes a concrete mechanism capable of checking or enforcing it.
- **Composition is not erasure.** Layers may contract internal structure, but must preserve the identity, responsibility, boundaries, and evidence needed by the enclosing assembly.
- **Evidence is not doctrine.** Tests, CAST records, observations, and validation may support or defeat current claims; they do not become normative solely by existing.
- **Skill graph is not tree projection.** A tree is one bounded view of a relation graph. Repetition in a projected branch does not duplicate the underlying skill identity.
- **Experience is not lesson is not skill.** Execution evidence may inform maintained knowledge; maintained knowledge may motivate a candidate artifact; neither transition activates executable instructions by itself.
- **Build selection is not runtime authority.** Skill points and prerequisites can govern one collection's build without granting Capability, Scope, Authority, Presence, or successful execution.

## SPELL

SPELL is a foundational lens, not a required schema surface.

### Spatial

The topological context: fields, domains, dimensions, boundaries, crossings, reach, Presence, and freedom of movement.

### Point

A distinction or direction of attention. A Point may be resolved or unresolved and may point into the unknown.

### Executable

The runtime context of participation and consequence: authority, responsibility, closure, execution, results, residuals, and observation.

### Language

The typological context: categories, distinctions, relations, relations of relations, interpretation, and freedom of meaning.

### Layer

The compositional context: parts, shapes, features, assemblies, stacks, bindings, and contraction into a larger whole.

## Domain ownership

The retained Agent Spells reference profile is assembled around five subject domains:

- **Spell** — declared possibility and Effect semantics.
- **Cast** — situated participation under the invariant casting law.
- **Familiar** — caster-owned dialect, attention, preference, stake, and advisory judgment.
- **Registry** — identity, addressability, carriers, books, libraries, provenance, and registrar relations.
- **Environment** — the context in which things can be observed, reached, made present, and supplied with concrete capabilities.

The repository root is the assembly over these domains. Root documents may govern the whole, but should not duplicate domain specifications.

`skilltree/` is a provisional Work surface above and across artifact formats,
not a silently adopted sixth Agent Spells domain. It may refer to Spells,
ordinary Skills, workflows, or repository-native artifacts through adapters.
Its collection graph, build accounting, lesson provenance, installation, and
execution boundaries must remain distinguishable.

## Artifact stake and lifecycle

Do not flatten Work, Knowledge, Code, Evidence, and Archive into one enum.

**Stake** answers what role an artifact plays:

- **Knowledge** — a current claim, definition, specification, contract, or explanation.
- **Code** — operational material that performs, interprets, checks, governs, or implements behavior.
- **Evidence** — attributable observations or records used to support, challenge, or falsify claims about Knowledge or Code.

**Lifecycle** answers how the artifact relates to the present:

- **Work** — provisional material still being proposed, investigated, or changed.
- **Current** — material presently relied upon for its stated authority.
- **Archive** — retained prior material whose identity and provenance matter but which no longer silently governs the present.

A test source is Code; a recorded test result is Evidence. A candidate specification is Work + Knowledge. A superseded CAST may be Archive + Evidence. These dimensions are intentionally orthogonal.

## Crossing rule

Moving an artifact between lifecycle roles is a meaningful crossing.

- Work becomes Current only through explicit adoption.
- Code does not become Evidence merely because it contains tests; an attributable run or observation is required.
- Evidence may defeat Current Knowledge without silently rewriting it.
- Current material becomes Archive only through explicit supersession or retirement.
- Archive does not regain Current authority without an explicit restoration or migration.

An invalid or implicit crossing should be noticeable rather than normalized away.

## Root surface

The intended root-facing contract is small:

- `README.md` — orientation.
- `FOUNDATIONS.md` — meaning and invariants.
- `AGENTS.md` — repository participation instructions for agents.
- `CLAUDE.md` — Claude-specific adaptation of those instructions.
- `SPELL.md` — present only when this repository/package itself declares a Spell.
- `.Binding` — present only when this repository/package is registered through a Registrar binding.

Absence of `SPELL.md` or `.Binding` is meaningful and should not be filled for symmetry.
