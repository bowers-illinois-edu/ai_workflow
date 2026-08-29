---
name: handoff
description: Turn this conversation into a paste-ready HANDOFF.md for a Claude Code session in Jake's repository: decisions, what was checked and what was only asserted, open questions, next step.
---

<!-- Synced against handoff_command.md at commit 2dcf3da (2026-08-29). -->

# Handoff to Claude Code

I use this app for thinking out loud --- often by voice, often walking --- and I
use Claude Code for work that touches files. This skill moves the first into
the second. When I ask for a handoff, produce the text of a `HANDOFF.md` that I
will paste into a repository, where a Claude Code session with no memory of
this conversation will read it and pick up the work.

That reader has my repository and does not have us. Everything the work depends
on has to be in the file, including things we settled so early in the
conversation that they now feel like background.

The Claude Code version of this command reports files changed and why, because
it changed them. You cannot. You have no working tree, no repository, and no
way to check a path. So do not name a file, a function, a line number, or a
section that I did not name first. Where the next session needs to find
something, say what to look for and let it search.

## What to write

Give me one block I can copy in a single gesture, in plain ASCII with
mathematics in LaTeX, headed `# Handoff` and dated. Ask which repository it is
going to and what I am calling the work, if I have not said. Then cover, in
this order:

- What we were doing and why: the question, the paper or project it serves,
  and what turns on the answer.
- What we decided, and the reason for each decision. A decision without its
  reason gets reopened by the next session, and I will not remember the reason
  either.
- What was checked, and how. Arithmetic put through numbers, a special case
  worked by hand, a simulation run --- name the check.
- What we only said. Everything asserted in conversation and never
  verified, listed separately and marked as unverified. Listing them is the main
  reason to write the file at all. A confident sentence spoken on a walk reads, three days
  later, exactly like a result.
- The open questions, each with the decision it blocks. "Whether the variance
  is over the assignment mechanism alone" is an open question; "whether we can
  report a standard error at all" is what it blocks.
- What the Claude Code session should do first: one concrete next action for the Claude Code session.
- Notation and definitions: every symbol the rest of the file uses.

## Restoring what voice mode dropped

A spoken conversation carries mathematics in words and drops subscripts.
Written down, "the expected value of the difference in means over the
assignment distribution" becomes `$E_{\mathbf{Z}}[\hat{\tau}]$`, and it needs
defining where it first appears. Do the same for anything I said aloud that has
a standard written form: estimator names, model specifications, R function
calls, file names I spelled out.

If the transcript left a claim ambiguous, and the ambiguity changes what the
next session should do, ask me before writing it down rather than choosing the
reading that makes the handoff tidy.

## Length

Long enough to be self-contained, and no filler. I would rather read three
paragraphs of setup I already know than have the next session guess at a
definition. Do not compress by dropping the reasons, the checks, or the
notation --- those are the parts a fresh session cannot reconstruct.
