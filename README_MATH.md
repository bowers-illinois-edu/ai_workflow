# README_MATH.md

How to use `CLAUDE_MATH.md` (and per-project supplements) with Claude Code.

## The files

- `~/repos/ai_workflow/CLAUDE.md` --- general writing preferences (ASCII, style, intellectual engagement). Shared across all projects.
- `~/repos/ai_workflow/CLAUDE_CODING.md` --- coding preferences (R, explanation over brevity). Shared across all projects.
- `~/repos/ai_workflow/CLAUDE_MATH.md` --- general mathematical-statistics discipline (modes, ledgers, theorem-use protocol, verification passes, working-with-Jake conventions). Shared across all projects.
- `<project-root>/CLAUDE_MATH.md` --- per-project supplement. Notation, key theorems with exact hypotheses, subfield-specific checks, running list of failure modes observed, annotated references. Section 16 of the general file explains what goes in one.

Two files share the name `CLAUDE_MATH.md`: one in the shared workflow repo, one in each project root. Their roles differ (general vs project-specific) and the file paths make it unambiguous.

## Three ways to wire it up

### Option 1: @-import in the project's CLAUDE.md

Claude Code's `CLAUDE.md` supports `@path` imports. Put at the top of each project's `CLAUDE.md`:

```
@/Users/jwbowers/repos/ai_workflow/CLAUDE.md
@/Users/jwbowers/repos/ai_workflow/CLAUDE_MATH.md
@./CLAUDE_MATH.md
```

Every session in that project auto-loads all three. Nothing to say at session start.

Tradeoff: everything loads every time, even for README edits or plotting. The math file is about 600 lines, so the cost is small but not zero.

### Option 2: Explicit invocation per session

Skip the import. At the start of a math-heavy session, say:

> "Read `/Users/jwbowers/repos/ai_workflow/CLAUDE_MATH.md` and the `CLAUDE_MATH.md` in this repo. We are working on propositions and proofs today."

Base context stays small for non-math work; the discipline loads only when you want it.

### Option 3: Hybrid (recommended)

Put the general writing file in `~/.claude/CLAUDE.md` (global) and keep the math files as explicit opt-in. Two reasons:

- Math work is a mode, not a default. Most coding, plotting, and prose sessions do not need it.
- Explicit loading is itself a useful ritual --- it signals to both you and Claude that the next work is slower and more careful.

## What to say at the start of a math session

One sentence that names the task, loads the discipline, names the project supplement, and picks the mode from section 2.1 of the general file:

> "Today we are deriving [X] / checking the proof of [Y] / looking for a counterexample to [Z]. Please read `~/repos/ai_workflow/CLAUDE_MATH.md` and this project's `CLAUDE_MATH.md`. Work in mode [Prove / Check / Explore / Write]. Ask me before guessing if the setup is ambiguous."

## Keeping the project supplement alive

A new project's supplement starts empty or close to it. The first time Claude (or you) makes a subfield-specific error, add a line. For example:

> "Failure mode 2026-04-19: claimed saddlepoint approximation without checking that the CGF was finite on a neighborhood of the relevant point. Always check CGF domain before invoking saddlepoint."

Over a project's life, the supplement becomes the accumulated memory of what-not-to-do-again. It is also where project-specific instruction updates live --- conventions, load-bearing references, recurrent danger zones --- rather than cluttering the general file.

## Quick reference

- Working on a specific project? Invoke all three: global `CLAUDE.md`, general `CLAUDE_MATH.md`, project `CLAUDE_MATH.md`.
- Starting a new paper? Create `CLAUDE_MATH.md` in the project root using the template in section 16.6 of the general file.
- Claude made a subfield-specific mistake? Add it to the project supplement before moving on.
- Changing modes mid-session (e.g., from Explore to Prove)? Say so; the mode changes what Claude should do.
