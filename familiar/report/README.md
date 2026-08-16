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

Binding here is a compositional pattern, not a universal permission edge. A semantic or evidentiary binding does not grant runtime authority and is not sufficient for Cast closure unless the owning runtime explicitly recognizes an admissible mechanism.

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
Carrier != content
Binding != authority
Knowledge != Evidence
Delivery != Closure
```
