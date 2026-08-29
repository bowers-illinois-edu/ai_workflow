# AI workflow

Jake Bowers's instruction set for working with Claude Code (and similar AI coding assistants). This repository is where I keep the canonical copy of the prompts, rules, and skills I load into sessions.

## Why this repository exists

I use Claude Code across statistics papers, R packages, code in several languages, teaching materials, and bibliography work. Each kind of work wants different defaults: a proof session and a code session should not behave the same way. Rather than re-type the same instructions every session --- or, worse, forget half of them --- I keep the rules in version control and load them by reference.

The repository started as a scratchpad ("a place to toss stuff I'm using as I learn how to use claude/codex") and has settled into an output style, one always-on file, one coding companion, and seven skills.

How a session finds its rules, in order: (1) the `Research` output style is
written into the system prompt itself, ahead of any instruction file, and
replaces the sentence that would otherwise define the session as software
engineering; (2) `~/.claude/CLAUDE.md` (symlinked
to a local clone of this repo) loads at startup and `@`-imports the coding rules; (3) the seven
skill descriptions sit in context and pull in a full protocol when its task
appears or when invoked by name; (4) a project repo's own `CLAUDE.md` adds
project facts, and math-heavy projects add a `CLAUDE_MATH.md` supplement that
overlays the math skill; (5) `HANDOFF.md` carries session-to-session working
state. Each rule is stated in exactly one place. The failure mode this layout
guards against is the stale local copy that silently competes with the ground
truth.

## Layout

Two kinds of instruction live here, split by when they should load.

**Always-on rules** load at the start of every session:

- **`output-styles/research.md`** --- the `Research` output style, which frames
  a session as research work spanning code, mathematics, and prose rather than
  as software engineering. It states nothing about tone, style, or testing,
  deferring to the two files below, so no rule is written twice. Symlinked to
  `~/.claude/output-styles/research.md` and selected in `/config`.
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

A third group, `claude_app/`, ports the always-on rules to the Claude app, which has no output styles and reaches the same rules through different slots. See "The Claude app" under Installing.

A fourth group, `chat_stats_config/`, sets up a chat --- in ChatGPT or in Claude --- for learning statistics and stress-testing research ideas. It is the one part of this repository that configures a tool Anthropic does not make. See "Statistics chats in the Claude app and ChatGPT" under Installing.

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

### The output style

```bash
mkdir -p ~/.claude/output-styles
ln -s /path/to/this/repo/output-styles/research.md ~/.claude/output-styles/research.md
```

Then run `/config` and choose "Research" in the Output style row. The name shown
in the picker comes from the `name:` field in the file's frontmatter, not from
the filename.

Claude Code merges settings from five scopes, in ascending precedence: user
(`~/.claude/settings.json`), project (`.claude/settings.json`), project-local
(`.claude/settings.local.json`), command-line flags, and managed policy. Put
`"outputStyle": "Research"` in the user file so it applies to every project. If
one repo ignores the style while the picker still lists it, look for a stray
`"outputStyle"` in that repo's `.claude/settings.local.json`, because that scope
beats the user file and shadows the default in that repo alone. A global
gitignore usually excludes `settings.local.json`, which makes such a pin harder
to notice rather than easier.

### The skills

```bash
mkdir -p ~/.claude/skills
for s in math verify-citations reviewer2 review-response decks style-audit simulation-study first-reader; do
  ln -sfn /path/to/this/repo/skills/$s ~/.claude/skills/$s
done
```

`first-reader` needs one step the others do not. It loads a persona from
`~/.claude/first-reader/persona.md`, which is deliberately outside this
repository because it quotes unpublished drafts. Jake keeps it in a private
repository:

```bash
git clone git@github.com:jwbowers/ai_workflow_private.git ~/repos/ai_workflow_private
ln -sfn ~/repos/ai_workflow_private/first-reader ~/.claude/first-reader
```

Anyone else should build their own by following
`skills/first-reader/METHOD.md`. Without a persona the skill loads and finds
nothing to read, while still reporting itself installed, so check that
`~/.claude/first-reader/persona.md` resolves before relying on it.

The corpus the persona is built from goes in neither repository. It writes to
`~/Claude_Transcript_Archive/`, beside a permanent additive archive of the
transcripts themselves. `make archive` updates both, and
`make install-archive-agent` schedules that daily. See `scripts/README` in the
archive directory for why it is not in Dropbox.

Symlinking (rather than copying) keeps the repo the single source of truth: edits here take effect in the next session, and `git log` stays the history of the rules.

Skills also work outside Claude Code: any assistant that can read files can be told "read `/path/to/this/repo/skills/verify-citations/SKILL.md` and follow it."

### Per-project supplements

A project repo carries its own `CLAUDE.md` (auto-loaded by Claude Code when working in that repo) holding project facts only --- build commands, layout, ground truth --- plus, for math-heavy projects, a `CLAUDE_MATH.md` supplement that overlays the math skill with the project's notation, key theorems, and subfield-specific checks. The supplement template is in `skills/math/references/supplements.md`. Live examples are in `~/repos/fastperm-paper/` (saddlepoint/tilting/orbit checks) and `~/repos/manytests-paper/` (FWER regimes, weak/strong control discipline). Project repos should not copy the global writing or coding rules --- those load globally, and a local copy goes stale and silently competes with the ground truth.

### The Claude app (phone and desktop)

The app has no output styles, so the first piece of the setup above does not
transfer. It reaches the other two layers through its own slots: account-wide
instructions that apply to every conversation, and skills that load when their
task appears, which is the same division Claude Code makes between `CLAUDE.md`
and `skills/`.

- **`claude_app/1_personal_preferences.md`** --- paste into "Instructions for
  Claude," reached by clicking your initials in the lower left corner, then
  Settings. That field applies to every conversation, so it carries the rules
  that matter everywhere: who I am, ASCII only, how to disagree with me, the
  compression rules, and three sentences of coding rules. Its header says what
  to cut first if the field rejects the text for length, and everything below
  the line of dashes is the text to paste.
- **`claude_app/skills/bowers-prose/`** --- the craft apparatus from `CLAUDE.md`
  followed by the three passages of my own prose: Gopen and Swan, technical
  exposition, the non-negotiables for editing my writing, the substitution and
  deletion tests.
- **`claude_app/skills/bowers-code/`** --- `CLAUDE_CODING.md` translated for a
  place with no working tree, so "read the files first" becomes "ask me for the
  files."
- **`claude_app/skills/style-audit/`** --- the audit procedure, converted from
  `skills/style-audit/SKILL.md`. Four things change in the app version: the
  description is cut to the 200-character limit, the references to the global
  `CLAUDE.md` name the app's two writing-rule slots instead, Pass 1 runs the
  scanner over an attached file, and Pass 1 gains a fallback for when the
  scanner cannot run.
- **`claude_app/skills/math/`** --- the mathematical discipline for a place
  where I am usually walking with the phone in voice mode. The Claude Code
  version assumes a screen, `.tex` files, and a simulation I can run; this one
  assumes a spoken answer and no files, so it adds how to say mathematics
  aloud, how to read a transcript back before working from it, what can and
  cannot be checked here, and how to draft the memo I will carry into Claude
  Code. Sections 4--16 are not rewritten: `references/` is a symlink to the
  Claude Code skill's, so the app loads the same files.
- **`claude_app/skills/handoff/`** --- the bridge I actually use from a
  conversation here to a session in Claude Code. It is not the `/handoff`
  command translated. That command reports the files it changed, and the app
  changed none; this skill produces the text of a `HANDOFF.md` for me to paste,
  and its distinctive requirement is that it keep what we checked separate from
  what we only said, so a sentence spoken on a walk does not reach the
  repository looking like a result.
- **`claude_app/3_custom_style.md`** --- the same three passages, formatted for
  a custom style. The app appears to have dropped that feature, so the file is
  kept rather than installed.

`bowers-prose`, `bowers-code`, and `handoff` bundle nothing, because they are
instructions and have nothing to run. `style-audit` bundles the scanner: the
app can run Python inside a skill, and the scanner needs no network, only a
file and a list of patterns. Whether it runs there is untested, which is why
the skill tells the auditor what to do when it does not. `math` bundles no
script either, and its `references/` are prose the app reads on demand.

Two app skills reach the Claude Code originals by symlink rather than by copy:
`style-audit/scripts/` points at the one directory holding `style_scan.py`, and
`math/references/` at the one directory holding sections 4--16. `zip -r` stores
what a symlink points at and the plugin installer resolves it too, so both
routes ship the same files Claude Code runs and there is no second copy to go
stale.

```bash
make app-skills   # writes one zip per directory in claude_app/skills/
```

Upload each zip in the app under `Customize > Skills`, with the "+" button, then
"+ Create skill," then "Upload a skill." This needs `Settings > Capabilities`
to have "Code execution and file creation" switched on, or no skills appear at
all. The zip has to hold the skill folder at its root, which is what the target
builds, and the folder name has to match the `name` in the frontmatter. The
frontmatter `description` is capped at 200 characters, and it is the only thing
the app reads when deciding whether a skill applies, so it has to carry the
trigger words.

Everywhere else in this repository a rule is stated once and loaded by
reference. These files cannot work that way, because the app cannot read a file
on my laptop: the rules have to be pasted or uploaded, and a pasted rule is a
copy that can go stale. They are not copies in any case. They are translations,
rewritten in the first person and cut to fit.

Because no program can compare a translation against its source, the sync stamps
carry a weaker guarantee than that. Each file records the commit of `CLAUDE.md`
or `CLAUDE_CODING.md` it was last synced against, in a header line for the
pasted blocks and an HTML comment for the skills, so the record never reaches
the app as instructions. `make check-claude-app` reads those stamps and prints
the commits that have touched the sources since, exiting nonzero when anything
is behind or unstamped. It reports that a re-read is owed; the re-read is mine
to do, and afterwards I update the stamp to the commit the report names. `make
test` runs the offline unittest suites for this and the two skill scripts.

### Statistics chats in the Claude app and ChatGPT

`chat_stats_config/` holds a four-file setup for a long-running statistics chat:
an orientation to paste into a project's instruction field, a longer framework
and a concept map to upload as project files, and a README that maps the files
onto each app's slots and gives the bridge text that makes the pasted block
reach the uploaded ones. The same three files serve both apps, so the Claude
desktop app and ChatGPT differ only in what the slots are called and how you
reach them. The README gives the navigation for each --- the Claude half checked
against the live app on 24 August 2026, the ChatGPT half not --- plus a
description to search by when the labels move again.

This is the only setup here that configures a tool Anthropic does not make.
Read `chat_stats_config/README.md` for the mapping, the order to cut in if an
instruction field rejects the text for length, and the loop that keeps the
concept map current, which matters because neither app can write to an uploaded
file.

### As a plugin, in Claude Code or the app

The repository is also a plugin marketplace, which is a second way to install
everything above: one `add` instead of a set of symlinks, and updates by syncing
rather than by rebuilding. `.claude-plugin/marketplace.json` lists two plugins,
because a skill that is right in one place is wrong in the other. The app
version of the style audit tells the auditor to reread the writing rules in
Instructions for Claude, which do not exist in Claude Code; the Claude Code
version names `CLAUDE.md`, which does not exist in the app.

- **`plugins/ai-workflow`** --- the eight Claude Code skills and `/handoff`.
- **`plugins/ai-workflow-app`** --- `bowers-prose`, `bowers-code`, `handoff`,
  and the app versions of `style-audit` and `math`.

Neither plugin holds a second copy of anything. Each one's `skills/` is a
symlink to the real directory, `skills/` or `claude_app/skills/`, and the
installer follows it and copies the files.

In Claude Code:

```bash
claude plugin marketplace add bowers-illinois-edu/ai_workflow
claude plugin install ai-workflow@ai-workflow
```

In the app: `Customize > Plugins`, the "Add" button, then the GitHub repository.

Plugin skills are namespaced, so `/math` becomes `/ai-workflow:math`. Installing
the plugin while the symlinks in `~/.claude/skills/` are still there loads every
skill twice and pays their always-on cost twice, which `claude plugin details
ai-workflow` puts at about 590 tokens per session. Pick one route or the other.

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
