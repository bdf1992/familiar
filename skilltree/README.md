# Skill Tree Workbench

Status: **Work**. This is a skill-neutral receiving surface, not a sixth adopted
Agent Spells domain and not a promoted runtime generation.

The workbench answers one small question now: can a repository describe a
collection of executable or instructive artifacts, spend skill points against
their prerequisites, and render familiar tree views without making the tree or
the build grant runtime authority?

## Kernel boundary

`collection.schema.json` and `kernel.py` define the first closed slice:

```text
adapter-owned artifact references
        +
skill ids / prerequisites / point costs / lesson references
        |
        v
validated collection graph
        |
        +-> tree projection
        +-> immutable build transition + unlock receipt
```

The collection graph is canonical for this slice. A skill tree is a projection
of that graph. A skill with two prerequisites may appear in two displayed
branches without becoming two skills.

The kernel does **not**:

- discover, install, execute, or mutate an artifact;
- interpret `SKILL.md`, `SPELL.md`, a workflow, or a provider package;
- grant Capability, Scope, Authority, Presence, or successful execution;
- decide that a lesson is true or that a proposed skill is better;
- equate skill points with Mana, money, tokens, time, or runtime capacity.

Those are adapter, Environment, evaluation, and governance boundaries. An
unlock receipt establishes only that one build transition satisfied the exact
content-derived collection revision, prerequisites, and point budget. It does
not establish the bytes behind an artifact locator unless its adapter reference
also carries a digest.

## Learning separation

The receiving shape adopts WikiSkill's useful three-way separation while
keeping Familiar's evidence and authority laws:

```text
execution evidence != persistent lesson != executable skill artifact
```

The intended evolution loop is:

```text
immutable execution references
        |
        v
maintained lessons and recurring patterns
        |
        v
one candidate artifact mutation
        |
        v
independent evaluation + explicit gate receipt
        |
        +-> accepted active revision
        +-> rejected candidate; lesson history remains
```

`lesson_refs` lets a node point back to the knowledge that motivated it without
copying that knowledge into executable instructions. The kernel treats those
references as inert provenance. A future maintainer may revise a lesson, and a
future proposer may mint a candidate artifact, but neither can activate its own
proposal merely by writing it.

This is deliberately narrower than the WikiSkill experimental harness:

- raw material may be an exact `CAST` record or an adapter-owned execution
  receipt rather than a copied model reasoning trace;
- validation policy is a plug-in boundary rather than a hard-coded scalar score;
- the inference agent need not receive the complete lesson store;
- accepted and rejected artifact revisions need attributable gate receipts;
- tree position, lesson frequency, and evaluation success grant no runtime
  authority.

## Adapter ports

The next implementation may add adapters behind these five roles without
changing the kernel objects:

| Port | Input | Output | Must not do |
|---|---|---|---|
| Discover | repository or registry root | artifact references | infer execution fitness |
| Observe | provider-specific run | immutable execution reference | treat executor self-report as outcome |
| Maintain | execution references + existing lessons | candidate lesson patch | activate a skill |
| Mint | lessons + selected evidence + current artifact | one candidate artifact revision | install it |
| Gate | candidate + declared evaluation policy | accepted/rejected receipt | rewrite the evidence or lesson history |

Agent Skills, Agent Spells, Claude skills, Codex skills, MCP-backed workflows,
and repositories such as Soveraeign can therefore participate through adapters.
The adapter string in `ArtifactRef` is open on purpose; the kernel preserves its
identity but does not pretend to understand its format.

## Load-bearing distinctions

```text
skill graph != tree projection
collection != build
unlock != install
install != execute
experience != lesson
lesson != skill
proposal != active revision
evaluation evidence != authority
Familiar guidance != runtime authority
```

The existing Agent Spells crossing remains a useful machine-checkable artifact
and evidence producer. It is one possible downstream adapter/reference profile,
not the ontology of every skill.
