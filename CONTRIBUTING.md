# Contributing

This repository treats work metadata as a control surface over the five subject domains. Metadata should make work, dependencies, lifecycle crossings, and residuals visible without turning GitHub bookkeeping into domain doctrine.

`FOUNDATIONS.md` remains authoritative for domain ownership, Stake, Lifecycle, and Crossing semantics. This file governs how repository work is represented.

## Work item contract

Every active issue must begin with a `## Metadata` block containing:

```text
- **Type:** bug | enhancement | documentation
- **Priority:** P0 | P1 | P2 | P3
- **Domain:** Spell | Cast | Familiar | Registry | Environment | Repository | Cross-domain
- **Depends on:** none | #issue references
- **Blocks:** none | #issue references
- **Related:** none | #issue references
```

The issue must also contain `## Problem`, `## Specification`, and `## Acceptance criteria` sections. Use `none` when a relation is genuinely absent; do not omit the field.

### Priority

Priority describes consequence, not effort or preferred implementation order.

- **P0 — correctness boundary:** a current invariant, authority, scope, conservation, replay, integrity, or fail-closed defect that prevents the repository from honestly claiming trustworthy execution on the affected path.
- **P1 — required integration/integrity:** necessary work for a supported user path, exact reference/evidence semantics, or integration claim, but not an immediately exploitable correctness-boundary escape.
- **P2 — portability/governance/maintainability:** supported-platform correctness, repository governance, lifecycle hygiene, or structural debt that should be repaired but does not currently outrank P0/P1 consequence work.
- **P3 — exploratory/optional:** bounded investigation or optional improvement that is active but does not currently block a supported claim.

Priority may change when evidence changes. When it does, update the issue metadata rather than leaving the old priority as historical truth.

### Dependencies and links

- `Depends on` means this issue should not claim completion until the referenced prerequisite is satisfied.
- `Blocks` is the inverse operational view: work whose trustworthy completion depends on this issue.
- `Related` is informative adjacency and must not be interpreted as a dependency.

Prefer issue references over duplicated prose. If the dependency changes, update both sides when doing so improves legibility.

## Repository artifact metadata

Do **not** add lifecycle front matter to every code or specification file merely for symmetry.

Repository-wide artifact Stake and Lifecycle are inventoried in `REPOSITORY_AUDIT.md`. Domain files own their technical meaning. GitHub issues own active repair specifications and backlog state. Pull requests own the attributable crossing from one repository state to another.

A change that creates, promotes, supersedes, archives, or materially changes the authority of an artifact must make that lifecycle effect visible in the pull request and update `REPOSITORY_AUDIT.md` when the current inventory would otherwise become false. If the audit cannot be updated in the same change, link an active issue that owns the residual.

## Residual law

GitHub Issues are the backlog source of truth for known non-deferred residuals.

- Do not create free-floating TODO prose that duplicates an active issue.
- Tests may preserve an executable defect specimen, but the issue owns the repair specification and acceptance criteria.
- Documentation may state a current limitation and link the issue; it should not maintain a second independent backlog.
- Closing an issue requires either satisfying its acceptance criteria or an explicit `not planned` / duplicate decision. Do not make unfinished work disappear by deleting the reference.

## Pull request contract

Every pull request must state:

- the issue it closes or references, or `none` with a reason for truly trivial repository maintenance;
- affected domain(s);
- whether a Lifecycle crossing occurs (`none` is explicit);
- whether `REPOSITORY_AUDIT.md` changes or which issue owns the audit residual;
- validation/evidence performed;
- remaining residuals, or `none`.

Use `.github/PULL_REQUEST_TEMPLATE.md`. The governance workflow validates these fields on every pull request.

## Automation

`.github/workflows/work-metadata.yml` keeps the control surface from decaying:

- validates issue metadata when issues are opened, edited, or reopened;
- synchronizes the issue Type label and a `priority:P0` ... `priority:P3` label;
- marks malformed issues `invalid` until repaired;
- validates pull-request work/lifecycle/evidence metadata as a check;
- periodically rescans open issues so metadata drift remains noticeable.

The workflow is a guard, not a substitute for judgment. A syntactically valid `P0` is still wrong if the consequence does not justify P0.

## Agent participation

Agents must follow `AGENTS.md` in addition to this contract. In particular, do not invent a new root concept when an issue, domain artifact, or audit entry already owns the concern.