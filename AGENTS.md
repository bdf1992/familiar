# Agent Participation

Work in this repository by preserving the distinctions in `FOUNDATIONS.md`.

## Before changing anything

1. Read `README.md` for the current practitioner path.
2. Read `FOUNDATIONS.md` for invariant distinctions and domain ownership.
3. Identify the owning domain: Spell, Cast, Familiar, Registry, Environment, or root Assembly.
4. Check `REPOSITORY_AUDIT.md` before creating a new root concept or duplicate surface.

## Change law

- Do not turn a Skill or Technique into a Spell merely by naming it one.
- Do not treat registration, publication, resolution, or Presence as casting.
- Do not let Familiar preference alter Spell semantics or runtime authority.
- Do not claim a Requirement is enforced unless the Environment exposes a concrete mechanism and the consequence path cannot bypass it.
- Do not silently promote Work to Current or Current to Archive.
- Preserve exact evidence and residuals; test source is Code, an attributable run is Evidence.
- Prefer the smallest change that closes a demonstrated gap.

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
