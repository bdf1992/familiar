# Agent Participation

Work in this repository by preserving the distinctions in `FOUNDATIONS.md` and the repository work contract in `CONTRIBUTING.md`.

## Before changing anything

1. Read `README.md` for the current practitioner path.
2. Read `FOUNDATIONS.md` for invariant distinctions and domain ownership.
3. Read `CONTRIBUTING.md` for work metadata, priority, dependency, lifecycle, and residual rules.
4. Identify the owning domain: Spell, Cast, Familiar, Registry, Environment, or root Assembly.
5. Check `REPOSITORY_AUDIT.md` before creating a new root concept or duplicate surface.
6. Check open GitHub Issues before creating a new residual. Prefer linking or refining an existing issue over duplicating backlog prose.

## Change law

- Do not turn a Skill or Technique into a Spell merely by naming it one.
- Do not treat registration, publication, resolution, or Presence as casting.
- Do not let Familiar preference alter Spell semantics or runtime authority.
- Do not claim a Requirement is enforced unless the Environment exposes a concrete mechanism and the consequence path cannot bypass it.
- Do not silently promote Work to Current or Current to Archive.
- Preserve exact evidence and residuals; test source is Code, an attributable run is Evidence.
- Prefer the smallest change that closes a demonstrated gap.
- Every known non-deferred residual must have one owning GitHub issue. Code or documentation may link that issue but must not maintain an independent backlog copy.
- Keep issue `Type`, `Priority`, `Domain`, `Depends on`, `Blocks`, and `Related` metadata current as evidence or dependencies change.
- Every pull request must state its issue relation, affected domains, Lifecycle crossing, audit impact, validation, and remaining residuals.
- If a change makes `REPOSITORY_AUDIT.md` materially false, update the audit in the same change or link the active issue that owns the audit residual.

## Domain direction

```text
Spell -----------┐
Familiar --------┤
Registry --------┼──> Cast
Environment -----┘
```

Cast is the situated composition point. It may consume domain contracts but should not own them.

## First Familiar boundary

The first practitioner path is `find-familiar@0.1.0`.

- preparation may propose and redraw candidates;
- the practitioner must explicitly accept one complete candidate before closure;
- only the accepted candidate may be persisted;
- persistence returns an exact `FamiliarRef`;
- reopening must reconstruct the same artifact or fail noticeably.

Never pre-author the practitioner's Familiar as though it were already accepted.

## Local data

Do not commit practitioner Spellbooks, Familiars, CAST records, or other private runtime data. Prefer OS user-data locations. Repository-local development data belongs only under `.agent-spells-local/` and must remain ignored.

## Validation

Run the complete suite after runtime or contract changes:

```bash
PYTHONPATH=cast:environment:. python -m unittest discover -s cast/tests -v
```

On PowerShell use `cast;environment;.` for `PYTHONPATH`.

Do not bypass `.github/workflows/work-metadata.yml` failures by deleting required metadata. Repair the work item or pull-request metadata instead.
