# Spell Domain

Spell owns declared possibility: portable Effect semantics, Telemetry declarations, Requirements, and the craft used to author or repair those declarations.

It may describe Spatial, Point, Executable, Language, and Layer concerns where they materially affect selection, inspection, gating, governance, or confirmation. It does not own live runtime truth, caster preference, or a particular implementation path.

Current material expected to settle here during reassembly:

- `format/`
- `spellcraft/`

A Spell declaration says what must remain true across valid Techniques. CAST evidence, runtime Situation, and Technique execution belong elsewhere.

## Semantic alignment

Schema validation, AST restrictions, sandbox conformance, fuzzing and unit tests can all pass while a generated implementation satisfies those tests through behaviour that defeats the declared Effect.

```text
structural validity   does it parse, type, and import within its constraints?
capability safety     can execution exceed the injected authority or scope?
behavioural evidence  what did it actually do across discriminating trials?
semantic effect       does it realize the declared Effect, on evidence
                      the candidate did not choose?
```

`alignment.py` defines the evidence obligations, not one evaluator. Independently generated adversarial cases, metamorphic and property tests, differential comparison, counterexample search, held-out trials, and explicit human acceptance are all conforming mechanisms.

**No candidate promotes itself.** Evidence whose provenance is the candidate is recorded and never counted, because a candidate supplying its own trials supplies the answer along with the question.

**Fail closed.** Absent required semantic evidence, promotion is refused rather than deferred: "we could not tell" and "it is fine" are the two states this layer exists to keep apart.

Human acceptance is one evidence source among others, available at any stake and required only where policy says so. Requiring a person for every low-stake synthesis is not what fail-closed means.
