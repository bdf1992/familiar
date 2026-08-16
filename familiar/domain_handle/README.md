# Domain Handle — Work

Issue #67 owns this bounded Familiar-domain experiment. It does **not** make
`CONTEXT.md`, `FAMILIAR.md`, or `HandleView` Current protocol interfaces.

The question under test is small:

> Can a charted Context and learned Domain Familiarity be resolved with an
> optional Subject Familiar into a useful read-only participant projection
> without flattening their identities or gaining runtime authority?

```text
Context ---------------------┐
                             ├──> Domain Handle View
Domain Familiarity ----------┤       inspect / orient only
                             │
optional Subject Familiar ---┘
```

## Distinctions

```text
Context != Environment
Context != Domain Familiarity
Domain Familiarity != Subject Familiar
Subject Familiar != runtime authority
Handle View != Holding
inspection != Cast
```

The fixtures under `fixtures/` are machine-readable forms of the Work specimens
recorded in issue #66. They are anchored to one exact repository commit. They
are not generated live Environment truth.

`resolver.py` keeps Context and Domain Familiarity separately addressable,
computes exact content digests, retains disagreements and unknown/unobserved
regions, and allows a Subject Familiar to change only the participant
projection. Advisory authority is carried as advisory data while runtime
authority is explicitly empty.

The resolver intentionally has no Cast or Environment dependency. Situation
re-resolution against the actual Environment is the next coupling problem after
this read-only Handle specimen is proven; adding it here would make a knowledge
projection silently effectful.

## Current specimen

The Context fixture retains one real repository disagreement: the root README
still describes the #34 crossing-plan contract as unestablished, while merged
PR #63 and `cast/practitioner/crossing.py` establish the contract as Work and
explicitly state that it does not execute. The resolver preserves both claims
and their interpretation rather than choosing one silently.

Unknown and unobserved regions are first-class lists. Missing observation is not
converted to false, empty, or zero.

## Validation

`cast/tests/test_domain_handle_67.py` checks source identity, disagreement and
unknown preservation, copy isolation, subject-relative projection, anchor
mismatch refusal, explicit non-effectfulness, and the absence of Cast or
Environment imports.
