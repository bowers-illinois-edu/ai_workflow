---
name: first-reader
description: Read a draft the way Jake reads it --- linearly, at face value, stopping where comprehension breaks --- and report each stopping point as the question he would ask. Use alongside style-audit before a memo, plan, paper section, or long explanation goes to him, and whenever a document has been style-audited and still reads badly. Finds undefined referents, unmotivated passages, and false claims, which no word list can catch.
---

# First reader

`style-audit` checks a draft against offenders someone has already named.
This skill checks a draft against a reader.

The two find different things. Across 851 turns of Jake's transcripts from
June to August 2026, the reasons he stopped reading sort into thirteen
mechanisms. The two largest are a referent he cannot resolve and a sentence
that is substantively wrong, and together they account for about half of
every reaction he had. Neither is findable by pattern: the offending word is
different every time, and a false claim is a fact about the subject matter.
The categories the scanner can reach come to about one complaint in eight.

So run both, and run them for different things. The persona is ordered by
how often a failure occurs, so it owns what is frequent and depends on
context: the referent, the missing motivation, the false claim. It carries
nothing about a failure Jake met only twice in three months, and the
validated persona has no rule about a missing main verb anywhere in its 706
lines. Rare but nameable failures --- a verbless fragment, a unicode
character, a bold sentence opening a paragraph --- belong to the scanner,
which never forgets them. Neither pass covers the other's half.

`METHOD.md` records how the persona was built and how to rebuild it.

## When to run it

- Before any memo, plan, or paper section goes to Jake to read and decide from.
- After `style-audit` reports a document clean and the prose still reads
  badly. This is the case the pass exists for: on 26 August a memo was
  audited, the scanner called it clean, and he stopped on the second
  paragraph he reached.
- On text newly added to an already-audited document. The failures cluster
  in the newest prose.
- On your own chat replies, when he is reading them to make a decision. He
  has asked for this explicitly more than once.

## How to run it

Spawn a **fresh subagent**, not a fork of the current session, and give it
exactly two things: the persona and the draft.

```
Agent(subagent_type: "general-purpose", prompt: """
1. Read and follow this persona specification in full:
   ~/.claude/first-reader/persona.md
2. Read this draft: <path>
   It was written for <who receives it>. They have not read it yet.
3. Produce the report the persona specifies in its section 4.
Do not edit the file. Your final message is the report.
""")
```

Three parts of that matter, and the pass fails without each of them.

- **Fresh, not a fork.** A session that wrote or has already read the draft
  cannot read it cold, and reading it cold is the whole method. A fork
  inherits the contamination.
- **Name who receives the text.** Whether a term is jargon depends on who is
  reading. A term that is right for Jake is wrong for a first-year graduate
  student and wrong again for a referee. The persona checks terms against
  the named reader, so the name has to be supplied.
- **Do not hand it the catalog.** The persona says so itself, and the reason
  matters: a word list turns attention toward word-spotting, which is the
  failure this pass covers. Loading `style-audit` section 6 into the same
  agent collapses this pass back into the one it complements.

## What comes back

Findings in document order, each with a line number, the text quoted, the
question Jake would ask, what is missing, and a proposed fix or a settling
question. The report opens with the stopping point --- the first finding,
and how far he gets before hitting it --- because he reads top to bottom and
stops.

Treat the findings as candidates, the same way scanner hits are candidates.
On a held-out 200-line draft the pass returned 12 findings, 9 of them marked
confident and 3 borderline, and caught 3 of the 4 things Jake actually
stopped on. An earlier version without the calibration returned 38 findings
on the same draft and caught 2, so the number of findings is worth watching:
a report much above a dozen per 200 lines means the pass has drifted back to
reporting improvable prose rather than stopping points.

It still stops on prose he would read past --- 8 of 20 held-out control
sentences. Triage before he sees anything, and drop the borderline block
first. The measurements are in
`~/.claude/first-reader/evidence/validation.md`, including what they do not
establish, which is how often it catches what stops him.

## What it does not do

It models one reader, so it predicts what stops Jake and not what is wrong
with a draft in general. It is built entirely from complaints, so it has no
evidence about prose he read without objecting and cannot tell you a passage
is good. And it goes stale: rerun `scripts/mine_transcripts.py` and re-read
the new turns when the reactions start to look unfamiliar.

## Files

- `~/.claude/first-reader/persona.md` --- the model of the reader. Kept
  outside this repository because it quotes unpublished drafts.
- `~/.claude/first-reader/evidence/` --- the mechanism tally with turn
  numbers, and the validation run.
- `METHOD.md` --- how to build a persona like this from your own transcripts.
- `scripts/mine_transcripts.py` --- builds the corpus. `make test` covers it.
