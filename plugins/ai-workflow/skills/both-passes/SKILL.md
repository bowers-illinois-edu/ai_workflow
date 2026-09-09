---
name: both-passes
description: Run style-audit and first-reader on one draft in the order that lets both reports be used. Freeze a copy, start the slow reader on it, audit while it reads, edit once. Use when Jake asks for both passes, for the full review, or types the name. A request for a style pass alone goes to style-audit. A request to read a draft as Jake goes to first-reader. Do not load this skill for either one.
---

# Both passes

Two skills read a draft before it leaves Jake's desk, and they find different
things. `style-audit` checks the draft against offenders someone has already
named. `first-reader` reads it as Jake reads it and reports where he would
stop. Running both is the usual case before a memo, plan, or paper section
goes to him.

This skill says nothing about what either one looks for. It says only what
order to run them in, because in the wrong order the second report cannot be
used.

## Why the order matters

`first-reader` takes about ten minutes and `style-audit` comes back sooner, so
the tempting move is to start editing while the reader is still reading. Two
things go wrong when you do.

The reader's report quotes lines by number from the file it read. Edit that
file and the numbers move and the quoted sentences are gone, so the report
describes a document that no longer exists.

And every sentence written during those minutes is prose that nobody has read.
`first-reader/SKILL.md` records what happened on 2026-08-30. Jake listed 29
places where he stopped in one class note. 28 could be traced to a sentence,
and 16 of those were replacements an earlier review round had written. Editing while the reader reads produces the exact
material the reader was sent to find, and produces it too late for the reader
to see.

## The order

1. Copy the draft into the session scratchpad. Nobody edits the copy until
   both reports are in hand.
2. Spawn the `first-reader` agent the way `first-reader/SKILL.md` specifies,
   giving it the path to the copy rather than to the original.
3. While it reads, run `style-audit` on the copy, both of its phases. Phase 1
   is `style-audit/scripts/style_scan.py`, which matches patterns and decides
   nothing. Phase 2 is the reading: you go through the copy paragraph by
   paragraph and apply the substitution test. Phase 1 by itself is not a style
   audit, and it will report a hard-to-read draft clean.
4. Wait for the reader's report. Change nothing before it arrives.
5. Merge the two reports and edit once.

Both passes read the same frozen copy, so a line number means the same line in
both reports.

Starting the reader first is also what makes the wait bearable. Run in series,
its ten minutes come after the audit is done. Started together, you wait for
whichever finishes last.

## Merging the two reports

Where the two reports flag different sentences, there is nothing to merge.
Apply both.

Where they flag the same sentence, write the fix that answers the
`first-reader` finding first, because that finding says Jake stopped reading
there, and then check what you wrote against the `style-audit` catalog. A
clear sentence carrying a catalogued word is a smaller problem than a clean
sentence Jake stops on.

After the last edit, run phase 1 over the edited draft. It matches patterns
and rewrites nothing, so it can be run as often as you like. Do not send the
reader again. From here `first-reader/SKILL.md` governs: apply only deletions
and word swaps, because a sentence written after the last read is a sentence
nobody has read.

## What this skill does not do

It judges no writing. Every question about what counts as a fault belongs to
the two skills it orders.

It does not model the document's audience. When the draft is for students, a
referee, or a program officer, `first-reader` still predicts where Jake stops
and nobody else, and its own report has to say so.
