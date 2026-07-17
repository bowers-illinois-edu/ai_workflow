# AI workflow

Jake Bowers's instruction set for working with Claude Code (and similar AI coding assistants). This repository is where I keep the canonical copy of the prompts, rules, and skills I load into sessions.

## Why this repository exists

I use Claude Code across statistics papers, R packages, code in several languages, teaching materials, and bibliography work. Each kind of work wants different defaults: a proof session and a code session should not behave the same way. Rather than re-type the same instructions every session --- or, worse, forget half of them --- I keep the rules in version control and load them by reference.

The repository started as a scratchpad ("a place to toss stuff I'm using as I learn how to use claude/codex") and has settled into one always-on file, one coding companion, and seven skills.

How a session finds its rules, in order: (1) `~/.claude/CLAUDE.md` (symlinked
to a local clone of this repo) loads at startup and `@`-imports the coding rules; (2) the seven
skill descriptions sit in context and pull in a full protocol when its task
appears or when invoked by name; (3) a project repo's own `CLAUDE.md` adds
project facts, and math-heavy projects add a `CLAUDE_MATH.md` supplement that
overlays the math skill; (4) `HANDOFF.md` carries session-to-session working
state. Each rule is stated in exactly one place. The failure mode this layout
guards against is the stale local copy that silently competes with the ground
truth.

## Layout

Two kinds of instruction live here, split by when they should load.

**Always-on rules** load at the start of every session:

- **`CLAUDE.md`** --- user context, writing style, ASCII-only output,
  explanation preferences, intellectual engagement. Symlinked to
  `~/.claude/CLAUDE.md`, which Claude Code reads automatically.
- **`CLAUDE_CODING.md`** --- rules for code work in any language. `CLAUDE.md`
  imports it with an `@`-reference, so it loads whenever `CLAUDE.md` does.

**Task-triggered protocols** are kept in `skills/`, one directory per skill.
Claude Code keeps each skill's one-paragraph description in context in every
session and loads the full instructions when the description matches the task
or when the skill is invoked by name (`/math`, `/verify-citations`,
`/reviewer2`, `/review-response`):

- **`skills/math/`** --- proofs, derivations, theorem statements,
  counterexamples, mathematical-statistics prose. `SKILL.md` holds the core
  standard and the start-of-task protocol. `references/` holds the longer
  checklists (assumption discipline, theorem-use protocol, verification passes,
  prose rules, per-project supplements), loaded on demand. See `README_MATH.md`
  for the per-project supplement pattern.
- **`skills/verify-citations/`** --- the protocol for confirming that every
  citation in a draft is real, with correct metadata, before the draft leaves
  your desk. `scripts/verify_bib.py` (stdlib-only python3) automates the
  per-entry Crossref/OpenAlex/arXiv checks and drafts the verification log. The
  judgment calls stay manual.
- **`skills/reviewer2/`** --- a simulated referee report before submission: a
  panel of distinct referee personas plus a champion, a self-audit that grounds
  every objection in the paper's text, and a prioritized revision plan.
- **`skills/review-response/`** --- the response memo to actual reviewers after
  a decision, with LaTeX and Quarto templates in the same directory.
- **`skills/decks/`** --- slide decks in two modes (research talks, teaching),
  Beamer or Quarto revealjs detected from the project, with length profiles
  from a 12-minute conference slot to a multi-hour workshop.
- **`skills/style-audit/`** --- the writing rules in `CLAUDE.md`, retargeted as
  an audit of existing drafts: a mechanical scan (`scripts/style_scan.py` flags
  the named offenders, non-ASCII characters, and dash-semicolon collisions)
  followed by a judgment pass built on the substitution test. Findings come
  located, quoted, categorized, and paired with a proposed rewrite.
- **`skills/simulation-study/`** --- design, implementation, and reporting of
  Monte Carlo operating-characteristics studies: a design ledger before code,
  replications derived from a stated Monte Carlo error target, seed and
  parallel-RNG discipline, MC uncertainty on every reported number, and
  conclusions scoped to the simulated regimes.

The old top-level filenames (`CLAUDE_MATH.md`, `CLAUDE_BIB.md`, `CLAUDE_REVIEWER2.md`, `CLAUDE_REVIEW-RESPONSE.md`, the response templates) survive as symlinks into `skills/`, so older projects and habits that say "read CLAUDE_BIB.md" still land on the current content.

## Installing

Substitute your own path for `/path/to/this/repo/`.

### The always-on file

```bash
ln -s /path/to/this/repo/CLAUDE.md ~/.claude/CLAUDE.md
# for example:
# ln -s ~/repos/ai_workflow/CLAUDE.md ~/.claude/CLAUDE.md
```

If you fork this repo, edit the `@`-import path inside `CLAUDE.md`'s "Coding rules" section so it points at your clone.

### The skills

```bash
mkdir -p ~/.claude/skills
for s in math verify-citations reviewer2 review-response decks style-audit simulation-study; do
  ln -sfn /path/to/this/repo/skills/$s ~/.claude/skills/$s
done
```

Symlinking (rather than copying) keeps the repo the single source of truth: edits here take effect in the next session, and `git log` stays the history of the rules.

Skills also work outside Claude Code: any assistant that can read files can be told "read `/path/to/this/repo/skills/verify-citations/SKILL.md` and follow it."

### Per-project supplements

A project repo carries its own `CLAUDE.md` (auto-loaded by Claude Code when working in that repo) holding project facts only --- build commands, layout, ground truth --- plus, for math-heavy projects, a `CLAUDE_MATH.md` supplement that overlays the math skill with the project's notation, key theorems, and subfield-specific checks. The supplement template is in `skills/math/references/supplements.md`. Live examples are in `~/repos/fastperm-paper/` (saddlepoint/tilting/orbit checks) and `~/repos/manytests-paper/` (FWER regimes, weak/strong control discipline). Project repos should not copy the global writing or coding rules --- those load globally, and a local copy goes stale and silently competes with the ground truth.

## Installing the `/handoff` slash command

Claude Code reads slash commands from `~/.claude/commands/`. Each file in that directory becomes a command whose name is the filename without the extension. To install `/handoff`:

```
mkdir -p ~/.claude/commands
cp /path/to/this/repo/handoff_command.md ~/.claude/commands/handoff.md
```

The file in this repo is named `handoff_command.md` so it does not collide with the working-memory file `HANDOFF.md`. The file in `~/.claude/commands/` must be named after the command you want to invoke --- here, `handoff.md` so the command is `/handoff`.

Now, in any session, typing `/handoff` makes Claude write a thorough `HANDOFF.md` in the current working directory covering:

1. key decisions made,
2. files changed and why,
3. current blockers or open questions,
4. important context to preserve,
5. what is done vs. what remains.

I treat `HANDOFF.md` as session-local working memory: untracked by git (the repo's `.gitignore` excludes it), overwritten on each `/handoff` call. The point is that a fresh Claude instance reading it should be able to continue the work without back-and-forth.

Durable rules belong in `CLAUDE.md` and the skills. Durable project state belongs in Claude Code's memory system. `HANDOFF.md` is for the things that are too specific and too in-flight for either of those.

## Inspiration

- https://sankalp.bearblog.dev/my-experience-with-claude-code-20-and-how-to-get-better-at-using-coding-agents/ --- especially the `/handoff` skill idea.
- https://github.com/scunning1975/MixtapeTools and https://causalinf.substack.com/p/claude-code-part-11-use-this-prompt
