# README_MATH.md

How the math discipline loads in Claude Code, and how per-project
supplements extend it.

## The files

- `~/repos/ai_workflow/skills/math/` --- the general
  mathematical-statistics discipline, packaged as a skill. `SKILL.md` holds
  the core standard, the start-of-task protocol, the setup ledgers, and the
  working-with-Jake conventions; `references/` holds the longer checklists
  (assumption discipline and theorem statements, theorem-use protocol and
  failure modes, verification passes and citation rules, prose rules,
  supplement rules), loaded on demand. Section numbers run in one sequence
  across the files, so "section 12" means the same thing everywhere.
- `<project-root>/CLAUDE_MATH.md` --- the per-project supplement: notation,
  key theorems with exact hypotheses, subfield-specific checks, a running
  list of failure modes observed in that project, annotated references.
  Section 16 of the general skill (`references/supplements.md`) explains
  what goes in one and includes the starter template (16.6).
- `<project-root>/CLAUDE.md` --- the project file Claude Code auto-loads in
  that repo. It holds project facts and points math work at the supplement.

The top-level `CLAUDE_MATH.md` in this repo is now just a compatibility
symlink into `skills/math/SKILL.md`, kept so older habits and older project
notes that name that path still resolve.

## How it loads

Nothing needs to be said to get the general discipline. The skill's
description sits in every session's context, and the full skill loads when
math work appears ("prove," "derive," "estimand," "randomization
inference," LaTeX math, `.tex` files) or when invoked directly as `/math`.

The project supplement loads by reference: the project's `CLAUDE.md` names
it (see `~/repos/fastperm-paper/CLAUDE.md` for the pattern), and a session
doing nontrivial math in that repo reads it alongside the skill. Live
examples of the pair:

- `~/repos/fastperm-paper/CLAUDE_MATH.md` --- saddlepoint/Edgeworth checks,
  tilting and importance-sampling conditions, permutation-orbit checks per
  design, Gamma-sensitivity checks.
- `~/repos/manytests-paper/CLAUDE_MATH.md` --- the four-regime FWER
  framework, weak-vs-strong control discipline, alpha spending vs
  investing, Lean-proof correspondence.

Explicit loading remains available and is still a useful ritual when the
work is about to get slow and careful:

> "Today we are deriving [X] / checking the proof of [Y] / looking for a
> counterexample to [Z]. Load the math skill and this project's
> `CLAUDE_MATH.md`. Work in mode [Prove / Check / Explore / Write]. Ask me
> before guessing if the setup is ambiguous."

That one sentence names the task, the supplement, and the mode from the
skill's section 2.1.

## Keeping the project supplement alive

A new project's supplement starts from the 16.6 template, mostly empty.
The first time Claude (or you) makes a subfield-specific error, add a line:

> "Failure mode 2026-04-19: claimed saddlepoint approximation without
> checking that the CGF was finite on a neighborhood of the relevant point.
> Always check CGF domain before invoking saddlepoint."

Over a project's life, the supplement becomes the accumulated memory of
what-not-to-do-again. It is also where project-specific conventions,
frequently invoked references, and recurrent danger zones live --- rather
than cluttering the general skill, which stays deliberately general.

## Quick reference

- Working on a specific project? The math skill triggers on its own; make
  sure the session also reads the project's `CLAUDE_MATH.md`.
- Starting a new paper? Create `CLAUDE_MATH.md` in the project root from
  the template in `skills/math/references/supplements.md` (16.6), and add
  a pointer section to the project's `CLAUDE.md`. Copy the pattern from
  fastperm-paper or manytests-paper.
- Claude made a subfield-specific mistake? Add it to the project
  supplement's failure-mode list before moving on.
- Changing modes mid-session (e.g., from Explore to Prove)? Say so; the
  mode changes what Claude should do.
- Simulation work in the same paper? That is the `simulation-study` skill;
  the supplement records only the project-specific sim conventions.
