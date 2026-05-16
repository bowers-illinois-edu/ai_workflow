# AI workflow

Jake Bowers's instruction set for working with Claude Code (and similar AI coding assistants). This repository is where I keep the canonical copy of the prompts, rules, and slash commands I load into sessions.

## Why this repository exists

I use Claude Code across statistics papers, R packages, code in several languages, teaching materials, and bibliography work. Each kind of work wants different defaults: a proof session and a refactor session should not behave the same way. Rather than re-type the same instructions every session --- or, worse, forget half of them --- I keep the rules in version control and load them by reference.

The repository started as a scratchpad ("a place to toss stuff I'm using as I learn how to use claude/codex") and has settled into four instruction files, one slash command, and a handful of drafts.

## The four CLAUDE files

- **`CLAUDE.md`** --- general rules that apply every session: user context, writing style, ASCII-only output, explanation preferences, intellectual engagement. It also contains a routing directive that names the three companions below and lists the cues that should trigger each one.

- **`CLAUDE_CODING.md`** --- rules for code work in any language (R, Python, Go, Rust, C, C++, Bash, Lua, Vimscript, JavaScript, TypeScript, SQL, and so on).

- **`CLAUDE_MATH.md`** --- rules for proofs, derivations, theorem statements, counterexamples, and substantive mathematical-statistics reasoning. See also `README_MATH.md` for the per-project supplement pattern.

- **`CLAUDE_BIB.md`** --- a verification protocol for confirming that every citation in a draft is real, with correct metadata, before the draft leaves your desk.

`CLAUDE.md` is meant to load in every conversation. The three `CLAUDE_*.md` companions are opt-in: each applies only when the work calls for it. A mixed-mode session --- code that does causal inference for a paper whose `.bib` also needs auditing --- loads all that apply. An extra file in context is cheap; working without the rules that apply is not.

## Installing the CLAUDE files

Pick whichever of these matches how you work. Substitute your own path for `/path/to/this/repo/`.

### Option 1: symlink `CLAUDE.md` into `~/.claude/` (what I do)

Claude Code loads `~/.claude/CLAUDE.md` automatically in every session. Symlink the repo's `CLAUDE.md` there so the rules apply everywhere and edits to either path affect the same file:

```
ln -s /path/to/this/repo/CLAUDE.md ~/.claude/CLAUDE.md
```

The three companions stay in the repo. The routing directive in `CLAUDE.md` tells Claude to read `CLAUDE_CODING.md`, `CLAUDE_MATH.md`, or `CLAUDE_BIB.md` when the cues for that file match.

If you fork this repo, edit the paths inside `CLAUDE.md`'s "Companion files" section so they point at your clone.

### Option 2: per-project `@`-import in a project's `CLAUDE.md`

Claude Code's `CLAUDE.md` files support `@path` imports. At the top of a project's `CLAUDE.md`, write:

```
@/path/to/this/repo/CLAUDE.md
@/path/to/this/repo/CLAUDE_MATH.md
@./CLAUDE_MATH.md
```

Every session in that project auto-loads all three. The third line is a per-project supplement; see `README_MATH.md` for the template.

Tradeoff: everything loads every session, even for plotting or a quick README edit. The math file is about 600 lines, so the cost is small but not zero.

### Option 3: explicit invocation per session

Skip auto-loading. At the start of a math-heavy or bibliography-heavy session, say:

> "Read `/path/to/this/repo/CLAUDE.md` and `/path/to/this/repo/CLAUDE_BIB.md`. We are verifying citations today."

Slower and more deliberate. Useful if most of your work does not need the full quartet, or if you want the explicit "now we are switching modes" ritual.

## When each companion should load

Each companion lists its own cues at the top of the file. Short version:

- **`CLAUDE_CODING.md`** --- code blocks in the user's message; file extensions like `.R`, `.py`, `.go`, `.rs`, `.c`, `.cpp`, `.sh`, `.lua`, `.vim`; error messages or stack traces; verbs like "implement," "refactor," "debug," "review this function," "build," "make this faster."

- **`CLAUDE_MATH.md`** --- "prove," "derive," "show that," "lemma," "theorem," "estimand," "identification," "asymptotic," "randomization inference"; LaTeX math (`$...$`, `\sum`, `\int`, `\mathbb{}`); `.tex` files in scope.

- **`CLAUDE_BIB.md`** --- "verify citations," "check the bibliography," "make sure these references are real"; mentions of `.bib` files, Crossref, OpenAlex, arXiv, ORCID, Google Scholar; "before I submit," "before I post," or "before I send this to a coauthor"; any session in which an AI assistant has drafted or edited references.

If the first message of a session is genuinely ambiguous, ask one short clarifying question rather than guessing.

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

I treat `HANDOFF.md` as session-local working memory: untracked by git (the repo's `.gitignore` excludes it), overwritten on each `/handoff` call. The point is that a fresh Claude instance reading it should be able to continue the work without back-and-forth. The current `HANDOFF.md` in this repo is itself an example of the format.

Durable rules belong in `CLAUDE.md` and its companions. Durable project state belongs in Claude Code's memory system. `HANDOFF.md` is for the things that are too specific and too in-flight for either of those.

## Other files in the repo

- `README_MATH.md` --- how to wire `CLAUDE_MATH.md` into specific project repos, and how to keep a per-project math supplement alive.
- `response_to_reviewers_template.qmd` / `.tex` --- starting points for drafting a response to reviewers.
- `AI_MATH.md`, `deck_generation_prompt*.md`, `rhetoric_of_decks.md`, `CLAUDE_REVIEW-RESPONSE.md` --- drafts and experiments I have not yet decided what to do with. Treat as scratch.

## Inspiration

- https://sankalp.bearblog.dev/my-experience-with-claude-code-20-and-how-to-get-better-at-using-coding-agents/ --- especially the `/handoff` skill idea.
- https://github.com/scunning1975/MixtapeTools and https://causalinf.substack.com/p/claude-code-part-11-use-this-prompt
