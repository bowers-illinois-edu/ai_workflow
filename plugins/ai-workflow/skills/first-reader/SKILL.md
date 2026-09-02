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
validated persona has no rule about a missing main verb anywhere in it. Rare but nameable failures --- a verbless fragment, a unicode
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
   Read it as Jake Bowers, who has not read it yet. If the document is for
   somebody else --- students, a referee, a program officer --- name them
   here as well, and say in the report that this pass does not model them.
3. Produce the report the persona specifies in its section 4.
Do not edit the draft. Write the report to <scratchpad path>, and also return
it as your final message.
""")
```

Ask for the report both ways, written to a file and returned as the final
message, because each one alone has lost a run. Telling the agent to write a
file loses the whole run when a write is refused: five runs during this
skill's own validation finished their reading and then went idle with nothing
on disk and nothing returned. Asking only for a message loses the run when no
message arrives: on 2026-08-28 a run that asked for the report only as its
final message went idle after about three minutes with no report, and a follow-up
asking for the report produced a second idle notification and nothing else.
Whether that agent wrote a report that was dropped on the way back or never
wrote one could not be determined. With both asked for, one failure is not
enough to lose the run --- a dropped message leaves a file behind, and a
refused write still leaves a returned message.

Name a path inside the session scratchpad directory, which the harness
supplies per session and describes as generally usable without permission
prompts. The ban on writing a file came from writes being refused. The
scratchpad answers that objection, and it was not available when the ban was
written.

Three parts of the spawn call matter, and the pass fails without each of them.

- **Fresh, not a fork.** A session that wrote or has already read the draft
  cannot read it cold, and reading it cold is the whole method. A fork
  inherits the contamination.
- **Name Jake as the reader, whatever the document's audience is.** The
  persona was built from 851 turns of his reactions and models no one else,
  so a run aimed at a different reader predicts nobody's stops. Measured on
  one class note: seven rounds on 2026-08-29 were told to read as a
  first-year student,
  because the note is for students, and the last of them could have seen 19
  of the items Jake stopped on the next morning and flagged none of them for
  his reason. A blind run told the reader was Jake caught four for his
  reason. Name him, and say in the report that the pass does not model the
  document's actual audience, so a note for students still needs a reader who
  is one.
- **Do not hand it the catalog.** The persona says so itself, and the reason
  matters: a word list turns attention toward word-spotting, which is the
  failure this pass covers. Loading `style-audit` section 6 into the same
  agent collapses this pass back into the one it complements.

## What comes back

Findings in document order, each with a line number, the text quoted, the
question Jake would ask, what is missing, and a proposed fix or a settling
question. The report opens with the stopping point --- the first finding,
and how far he gets before hitting it --- because he reads top to bottom and
stops. If the agent goes idle without returning a report, read the file at the
scratchpad path before spawning another run.

A replacement in the report is new prose that nobody has read as a reader.
On 2026-08-29 seven rounds ran on one class note and Jake read the result the
next morning: of the 28 stops that could be traced, 16 are sentences a round
wrote as its replacement and 6 more were written by the applying session after
the last round had read. So apply a replacement the way you would apply any
new draft --- read it cold, and prefer the shortest one that carries the
content --- and after the final read apply only deletions and word swaps. A
sentence written after the last pass is a sentence nobody has read. The
evidence is `~/.claude/first-reader/evidence/scoring_2026-08-30.md`.

Treat the findings as candidates, the same way scanner hits are candidates.
Two measurements say how good the candidates are. On a held-out 200-line
draft with four ground-truth stops taken from his chat complaints, the pass
returned 12 findings and caught 3 of the 4. On 2026-08-29 Jake read a
206-line memo himself and wrote down every stop before the pass ran --- 27
of them, one every four lines of prose --- and the pass returned 9 findings
and caught 3 of the 27. The misses were in the two families his rules name
first: a thing given a person's verb (nine misses) and a term he could not
resolve (five). The persona's count cap, tuned on the first test, suppressed
the second, and it has been removed. Expect the findings to run long on a
draft that reads badly, and do not read a long list as drift.

It still stops on prose he would read past --- 5 of the 9 findings on
2026-08-29, and 8 of 20 held-out control sentences before that. Triage
before he sees anything, and drop the borderline block first. The
measurements are in `~/.claude/first-reader/evidence/validation.md`. The
2026-08-29 test is the first with sensitivity measured against a linear
read, and its files are `ground_truth_2026-08-29.md`,
`report_two_models_2026-08-29.md`, and `scoring_2026-08-29.md` there.

## What it does not do

It models one reader, so it predicts what stops Jake and not what is wrong
with a draft in general, and it does not model anybody else: a note for
students, a paper for referees, or a memo for a program officer still needs a
reader drawn from that audience, which this pass cannot supply. It is built
entirely from complaints, so it has no
evidence about prose he read without objecting and cannot tell you a passage
is good. And it goes stale: rerun `scripts/mine_transcripts.py` and re-read
the new turns when the reactions start to look unfamiliar.

## Files

- `~/.claude/first-reader/persona.md` --- the model of the reader. It lives
  in the private `ai_workflow_private` repository, symlinked here, because it
  quotes unpublished drafts.
- `~/.claude/first-reader/evidence/` --- the mechanism tally with turn
  numbers, the pre-registered ground truth, and the validation run.
- `~/Claude_Transcript_Archive/` --- the corpus the persona was built from,
  beside a permanent archive of the transcripts it came from. In no
  repository, on purpose: it spans every project and is confidential
  throughout. A launchd agent refreshes both daily.
- `METHOD.md` --- how to build a persona like this from your own transcripts.
- `scripts/mine_transcripts.py` --- builds the corpus. `make test` covers it.
