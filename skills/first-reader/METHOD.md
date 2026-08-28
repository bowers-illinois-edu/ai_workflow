# How to build a reader model from your own transcripts

This file records the procedure that produced `persona.md`, in enough detail
that someone else can run it on their own Claude Code transcripts, and in
enough detail that Jake can run it again on a new machine.

## Why you would do this

A writing-rules file tells an assistant how to write. A style audit checks
prose against a list of offenders someone already named. Both help, and both
have the same limit: they only catch failures that have been named in
advance.

Jake ran into that limit in August 2026. He had a detailed `CLAUDE.md` and a
`style-audit` skill with a scanner, and he was still stopping several times
an hour on prose he could not read. When we counted the reasons he stopped
across three months of transcripts, the two biggest were an undefined
referent and a sentence that was substantively wrong. Neither can be found
by a pattern, because the offending word is different every time and the
false claim is a fact about the subject matter.

What can find them is a reader. The transcripts already contain thousands of
recorded reactions by one specific reader, which is the raw material for
simulating that reader. This procedure turns the transcripts into that
simulation, and then tests whether the simulation predicts reactions it was
never shown.

The output is not another rule file. It is a persona document plus the
evidence for it, run as a separate reading pass alongside the rule-based
audit rather than in place of it.

## Step 1. Build the corpus

```
python3 scripts/mine_transcripts.py --tail 0
```

The script walks `~/.claude/projects/*/*.jsonl` and writes one JSON object
per turn the person typed, each paired with the assistant prose that
preceded it. Options: `--root` for a different transcript directory,
`--since YYYY-MM-DD`, `--project SUBSTRING`, `--tail N` for how much
preceding prose to keep, and `--out` for where to write it.

With no `--out` it writes to `~/Claude_Transcript_Archive/corpus.jsonl`, or
to `$FIRST_READER_CORPUS` when that is set. Two places it deliberately avoids:
either repository, and anything under `~/Library/CloudStorage`. macOS denies a
background process access to the latter, so a scheduled refresh there fails
every night while working when run by hand.

Keep the corpus out of every repository, public or private. It spans every
project the person has used Claude Code on, which in Jake's case means other
people's unpublished work, graduate students' job materials, peer reviews
written under confidentiality, and personal medical notes, all in one file.
Nothing downstream needs it stored anywhere in particular, because rerunning
this one command rebuilds it.

Two things about this step matter more than they look.

- **Keep only what the person typed.** Most records in a transcript are
  machinery: tool calls, tool results, slash-command echoes, notifications
  from other agents, injected reminders. The script drops all of it. On
  Jake's transcripts, 10,941 user-role records held no prose at all and
  another 147 were notifications from other agents. Keeping any of that
  would have built a model of the harness rather than a model of the reader.
- **Pair each turn with the prose that provoked it.** A complaint on its own
  records the objection and not the sentence. A two-word reaction such as
  "what family?" teaches nothing until you can see the sentence above it
  ending in "belongs to the family," with no family named anywhere before
  it. The pair is the unit of evidence, and the persona is written from
  pairs.

Jake's corpus, run on 2026-08-28: 851 turns, 2026-06-05 to 2026-08-28, 27
projects, 190,454 characters. The transcript directory held 849 session
files and 630 MB in total, so the corpus is about 0.03 percent of what is on
disk.

## Step 2. Read all of it

Read every turn. Do not search it.

The temptation is to grep for complaint words --- "confusing," "unclear," "I
don't understand" --- and work from the hits. We tried that first, to size
the problem, and it found 124 turns out of 851. Reading all 851 showed why
that shortcut fails. Some of the sharpest reactions carry no complaint
vocabulary at all. The most important category after the undefined referent
is the substantive correction, and those typically open with a flat "No" and
then restate the subject matter correctly, with no word in them that any
list of complaint terms would match. A keyword search finds none of them.
At roughly 50,000 tokens for a three-month
corpus, reading all of it takes one long context window and is the step that
decides whether the model is any good.

## Step 3. Classify by mechanism, not by word

For each reaction, ask what broke for the reader, not which word offended.
Group the reactions into a small number of failure mechanisms and write down
the turn numbers in each group so anyone can check the classification.

This is the step where the temptation is to produce another list of banned
words, and where doing so would repeat the failure the whole exercise is
meant to fix. Jake had already learned this the hard way: when "load-bearing"
went on the list, the same habit came back as "lands," "runs along," and "the
edge." A list of words teaches avoidance of those words. A description of a
mechanism teaches recognition.

Jake's classification came out as thirteen mechanisms, of which two account
for about half of all reactions:

| What broke | Count |
|---|---|
| A referent the reader cannot resolve | 69 |
| A sentence that is substantively wrong | 28 |
| A passage with no reason to be there | 18 |
| A figure of speech standing in for a fact | 12 |
| A document, theory, or number acting like a person | 9 |
| A number asserted instead of derived | 8 |
| Announcing a claim instead of making it | 6 |
| Compression that reads as cryptic | 6 |
| A term before the content it names | 5 |
| A shorthand label where the full name belongs | 4 |
| A term the person reading has no use for | 4 |
| Prose that does not sound like the person's own | 3 |
| A phrase with no finite main verb | 2 |

Turn numbers for every row are in `evidence/mechanism_tally.md`. A turn
carrying two complaints appears in two rows, so the rows sum to more than
the number of turns classified.

## Step 4. Write the persona

The persona document has five parts. Keep it short enough to be read in full
by an agent that also has to read a draft.

1. **Who is reading.** Concrete facts that change what stops them: what
   training they have, which vocabulary they own, what they are reading for.
   Jake's version records that he learned statistics on his own, has one
   pass/fail semester of calculus, and owns "prior" and "posterior" but not
   "admissible" or "envelope."

2. **How they read.** Jake reads linearly, takes every sentence at face
   value, and stops at the first break rather than skimming past it. That
   single fact changes the report format: findings go in document order, not
   severity order, and the first one gets marked, because it decides whether
   the rest of the document is read at all.

3. **The questions to ask at each sentence.** One question per mechanism
   from step 3, phrased as something to ask, not something to avoid.

4. **The mechanisms, each anchored to verbatim pairs.** For each mechanism,
   two or three real (offending prose, actual reaction) pairs quoted exactly.
   The quotations do the work a definition cannot: they show the reaction in
   the reader's own voice, at the reader's own pitch.

5. **The report format, and what not to do.** Findings as questions the
   reader would ask, never as verdicts. No silent rewriting, and never a
   changed statistical claim.

One instruction belongs in the persona and is easy to leave out: **do not
load the rule-based catalog before this pass.** A word list turns attention
toward word-spotting, and word-spotting is the failure this pass exists to
cover.

## Step 5. Validate by retrodiction

Build the persona from the earlier part of the corpus and test it on
reactions it was never shown. Without this step you have a plausible
document and no evidence.

The test needs held-out drafts, not held-out complaints, because the real
task is reading a draft cold. Recover them from git:

1. Pick reactions from the last stretch of the corpus that name a document
   and quote a passage.
2. Find the commit holding the version the person actually read.
   `git log -S "<a phrase they quoted>"` locates it. Check that any line
   numbers they mentioned line up with that version, which confirms you have
   the right one.
3. Write down the ground truth --- every passage they stopped on, in their
   own words --- **before** running anything.
4. Run whatever rule-based pass already exists on the same file, as the
   baseline to beat.
5. Give a **fresh** agent the persona and the draft, and nothing else. Not a
   fork of the session that built the persona: that session has read the
   ground truth and cannot read the draft cold. A fresh agent with the
   persona document is the thing you are actually shipping.
6. Score hits against the ground truth, and count everything else the agent
   flagged. A pass that finds all four known problems and ninety others is
   not usable, so report the total, not just the hits.

One more requirement, and it is the easiest to miss: blind the author, not
just the reader. We got this wrong the first time. The first persona was written
after reading the whole corpus, held-out weeks included, and it then quoted
one of the held-out sentences as an example. The reading agent duly found
that sentence, which measured nothing: the answer had been written into the
question. Split the corpus by date first, and have the persona written by
someone --- a person or a fresh agent --- who has seen only the earlier part.

That split has a second use. Because the persona is a document rather than a
fitted model, a fresh agent can write it from the build set in a few minutes,
so the clean version takes about as long as the contaminated one.

One note on what the build set holds. Step 1 pairs each turn with the prose
that provoked it, and the persona is better for having both sides. The clean
rebuild here was given only the person's own turns, because that half is
small enough to read whole and because he quotes the offending sentence
himself often enough that much of the prose survives inside the complaint.
If a rebuilt persona misses ground truth that the full-corpus one caught,
the missing assistant side is the first thing to suspect.

Jake's run used two drafts from 24 and 26 August, both after the last
rewrite of his writing rules, with five ground-truth reactions between them.
Results are in `evidence/validation.md`.

## Step 6. Decide where the persona lives

The persona quotes the person's unpublished writing and their reactions to
it. That is the most personal artifact in this procedure, and the reason it
is worth checking before it goes anywhere public.

In Jake's case the method is in a public repository and the persona is not.
`scripts/`, `tests/`, this file, and `SKILL.md` contain no private
material and are shareable as they stand. `persona.md` quotes drafts of an
unpublished paper, so it is kept outside the public tree and `SKILL.md`
takes its path as a setting.

If you share a persona, scrub it first: replace third-party names with
roles, and drop quotations from anything unpublished that is not yours.

## What it took to build, and what it does not do

The whole procedure took one session: a few minutes of scripted extraction,
one long read, one drafting pass, and two validation agents. It needs no
fan-out across many agents. Using one would have added tokens without adding
evidence, because the judgment that decides the result happens in step 2 and
cannot be split without splitting the corpus that has to be read whole.

Three limits worth stating plainly.

The persona models one reader. It predicts what stops Jake, not what is
wrong with a draft in general, and a paper's actual readers are not Jake.
The `style-audit` pass and the persona pass answer different questions and
neither replaces the other.

It is built from complaints, so it is calibrated on failures and has no
evidence about what the person read without objecting. Nothing in the corpus
records approval, so the model cannot tell you that a passage is good.

It goes stale. The mechanisms come from a fixed window. Rerun step 1 and
re-read the new turns when the reactions start to look unfamiliar.
