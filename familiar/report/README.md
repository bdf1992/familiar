# Familiar Report — Work

A Familiar Report is a candidate account *about* a Familiar. It is intentionally not frozen as a schema yet.

The current working model is:

```text
Report = knowledge carrier + account bindings
```

For a Familiar Report, useful bindings include:

```text
about       -> exact FamiliarRef
based-on    -> Familiar state, CAST records, observations, corrections, or other attributable evidence
reported-by -> reporter
for         -> perspective / purpose / audience
```

## View is not Report

A Familiar View represents source Familiar guidance for a perspective. It may select, omit, summarize, translate, or rearrange that source while remaining source-bounded.

A Report goes further: it makes an accountable statement *about* the Familiar using a stated basis.

```text
Familiar View
    represents Familiar

Familiar Report
    accounts for Familiar
```

A host-facing projection needed immediately after Find Familiar is therefore usually a View, not a Report.

## Stake and evidence

A Report ordinarily occupies **Knowledge** stake. The records and observations it cites may occupy **Evidence** stake. Referencing Evidence does not turn the Report itself into Evidence, and Evidence does not become doctrine merely by appearing in a Report.

This follows the repository-wide distinction between artifact stake and lifecycle rather than inventing Report as a new domain.

## Carrier and Binding

`Scroll` remains the Registry-owned, Spell-specific carrier currently defined by `registry/scroll.schema.json`. Do not broaden Scroll merely to fit Reports.

Report is instead treated as a recognizable carrier assembly: bounded content made situated and accountable by bindings such as `about`, `based-on`, `reported-by`, and `for`.

These are **account bindings**: semantic/evidentiary relations over Knowledge. They do not replace domain-owned binding realizations.

```text
account binding
    situates knowledge

Registrar Binding
    situates registration/addressability

Technique Binding
    situates an execution path for a Spell Effect
```

The shared compositional intuition is a typed relation between addressable things. The owning domain determines what a relation means and what mechanisms, if any, it can participate in.

Binding here is therefore not a universal permission edge. A semantic or evidentiary binding does not grant runtime authority, establish Presence, realize an Effect, or become sufficient for Cast closure merely because the relation exists.

## Bound knowledge and admissibility

Account bindings do more than decorate content: they constrain the admissible reading of that content.

```text
"tests passed"
    unbound -> ambiguous claim

about       -> commit:abc123
based-on    -> workflow-run:991
reported-by -> github-actions
for         -> compatibility assessment

    bound -> situated claim
```

Each binding removes otherwise-plausible interpretations:

- `about` constrains which subject the account concerns;
- `based-on` constrains which evidence may be cited as its basis;
- `reported-by` preserves attribution rather than allowing the account to float free of its reporter;
- `for` constrains the perspective or question the account is answering.

This follows the broader working intuition that **Binding changes admissible candidates**. For Knowledge, that means changing admissible readings, references, or evidence relations—not changing truth itself.

```text
Bound != true
Bound != accepted
Bound != authorized
Bound != closed
```

A binding may make a statement precise enough to evaluate while leaving it unsupported, defeated, or irrelevant to a particular Cast Requirement. Operational consumers remain responsible for deciding which bound information is admissible for their own purpose.

## Presence

A Report may account for observations that a Familiar was Present, but the Report does not establish that Presence. Likewise a Familiar View may be consumed without the Familiar being Present.

```text
View != Presence
Report about Presence != Presence
Binding to Presence evidence != Summon Familiar
```

Presence belongs to the situated Environment/Cast side of the system; reporting about it remains knowledge-side work.

## Why no schema yet

The previous `familiar-report.schema.json` mixed two operations:

1. projecting Familiar guidance for a host; and
2. reporting claims and evidence about that Familiar.

The first operation now has the concrete `../view/familiar-view.schema.json` contract because it is needed immediately for portable host guidance.

The second should wait for real evidence-backed Familiar Reports so the format can be derived from specimens rather than anticipated fields.

## Candidate invariants

```text
Familiar != Familiar View
Familiar != Familiar Report
View != Report
View != Presence
Report about Presence != Presence
Carrier != content
Binding != truth
Binding != authority
Knowledge != Evidence
Delivery != Closure
```
